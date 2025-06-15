import requests
import json
import re
import time
import pickle
import os
from datetime import timedelta
import sys
import base64
import logging
import urllib.parse
import uuid
import random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstagramScraper:
    def __init__(self, update_mode=0):
        """Initialize the scraper with headers and session."""
        self.headers = {
            'x-ig-app-id': '936619743392459',
            'x-asbd-id': '198387',
            'x-ig-www-claim': '0',
            'origin': 'https://www.instagram.com',
            'accept': 'application/json',
            'user-agent': self.get_random_user_agent(),
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.instagram.com/',
            'accept-language': 'en-US,en;q=0.9',
            'connection': 'keep-alive',
            'dnt': '1',  # Do Not Track
            'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        self.proxies = {
            'http': os.getenv('HTTP_PROXY', ''),
            'https': os.getenv('HTTPS_PROXY', ''),
        }

        self.ig_story_regex = r'https?://(?:www\.)?instagram\.com/stories/([^/]+)(?:/(\d+))?/?'
        self.ig_highlights_regex = r'(?:https?://)?(?:www\.)?instagram\.com/s/(\w+)(?:\?story_media_id=(\d+)_(\d+))?'
        self.ig_profile_regex = r'https?://(?:www\.)?instagram\.com/([^/]+)/?$'

        # Initialize session with retries
        self.ig_session = self.create_requests_session()
        self.cookies = None
        self.csrf_token = None
        self.csrf_expiry = None
        self.csrf_cache_duration = timedelta(hours=1)
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.update_mode = update_mode  # Add update_mode parameter
        
    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'
        ]
        return random.choice(user_agents)
    def make_request(self, url, method='GET', data=None, headers=None, retries=3):
        headers = headers or self.headers.copy()
        for attempt in range(retries):
            try:
                headers['x-csrftoken'] = self.get_csrf_token()
                headers['user-agent'] = self.get_random_user_agent()
                headers['x-ig-www-claim'] = self.cookies.get('ig_did', '0')
                time.sleep(random.uniform(1, 3))  # Avoid rate limits
                if method == 'POST':
                    response = self.ig_session.post(url, headers=headers, data=data, proxies=self.proxies)
                else:
                    response = self.ig_session.get(url, headers=headers, proxies=self.proxies)
                if response.status_code == 401:
                    logger.warning("401 Unauthorized, attempting re-login")
                    self.ig_login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'), 'ig_cookies')
                    continue
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit (429), waiting {10 * (2 ** attempt)} seconds")
                    time.sleep(10 * (2 ** attempt))
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                time.sleep(2 ** attempt)
        raise SystemExit(f"Request failed after {retries} retries: {url}")
    
    def create_requests_session(self):
        """Create a requests session with retry logic."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def set_proxies(self, http_proxy: str, https_proxy: str) -> None:
        self.proxies['http'] = http_proxy
        self.proxies['https'] = https_proxy
        self.ig_session.proxies.update(self.proxies)

    def get_csrf_token(self):
        """Fetch CSRF token from Instagram login page or cookies."""
        try:
            # First, check existing cookies
            if 'csrftoken' in self.ig_session.cookies:
                logger.info("Using CSRF token from cookies")
                return self.ig_session.cookies['csrftoken']

            # Fetch login page
            response = self.ig_session.get('https://www.instagram.com/accounts/login', headers=self.headers, proxies=self.proxies)
            response.raise_for_status()

            # Try parsing JSON from sharedData
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script', string=re.compile('window._sharedData'))
            for script in script_tags:
                json_match = re.search(r'window._sharedData\s*=\s*({.+?});', script.text)
                if json_match:
                    data = json.loads(json_match.group(1))
                    if 'config' in data and 'csrf_token' in data['config']:
                        logger.info("CSRF token found in sharedData")
                        return data['config']['csrf_token']

            # Fallback to regex
            csrf_token_match = re.search(r'"csrf_token":"(\w+)"', response.text)
            if csrf_token_match:
                logger.info("CSRF token found via regex")
                return csrf_token_match.group(1)

            # Fallback to Selenium
            logger.warning("CSRF token not found, trying Selenium")
            driver = self.init_driver()
            driver.get('https://www.instagram.com/accounts/login/')
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            cookies = driver.get_cookies()
            driver.quit()
            for cookie in cookies:
                if cookie['name'] == 'csrftoken':
                    logger.info("CSRF token found via Selenium")
                    self.ig_session.cookies.set('csrftoken', cookie['value'])
                    return cookie['value']

            logger.error("CSRF token not found in response or cookies")
            raise ValueError("CSRF token not found")
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error fetching CSRF token: {e}")
            raise SystemExit('Error getting CSRF token')

    def ig_login(self, username: str, password: str, cookies_path: str) -> None:
        """Perform Instagram login if cookies don't exist or are invalid."""
        if self.ig_cookies_exist(cookies_path):
            logger.info('Loading saved cookies')
            try:
                response = self.ig_session.get('https://www.instagram.com/api/v1/users/web_profile_info/?username=instagram', headers=self.headers, proxies=self.proxies)
                if response.status_code == 200:
                    logger.info("Cookies are valid")
                    self.cookies = {cookie.name: cookie.value for cookie in self.ig_session.cookies}
                    return
                logger.warning("Cookies are invalid, performing login")
            except requests.RequestException:
                logger.warning("Cookies are invalid, performing login")

        # Try AJAX login first
        try:
            csrf_token = self.get_csrf_token()
            response = self.ig_session.get('https://www.instagram.com/accounts/login', headers=self.headers, proxies=self.proxies)
            response.raise_for_status()
            login_text = response.text
            rollout_hash_match = re.search(r'"rollout_hash":"(\w+)"', login_text)
            if not rollout_hash_match:
                logger.error("Could not find rollout_hash")
                raise ValueError("Missing rollout_hash")
            rollout_hash = rollout_hash_match.group(1)

            login_headers = self.headers.copy()
            login_headers.update({
                'x-requested-with': 'XMLHttpRequest',
                'x-csrftoken': csrf_token,
                'x-instagram-ajax': rollout_hash,
                'referer': 'https://www.instagram.com/',
            })

            login_payload = {
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'username': username,
                'queryParams': '{}',
                'optIntoOneTap': 'false',
                'stopDeletionNonce': '',
                'trustedDeviceRecords': '{}',
            }

            response = self.ig_session.post('https://www.instagram.com/accounts/login/ajax/', headers=login_headers, data=login_payload)
            response.raise_for_status()
            login_json = response.json()
            if login_json.get('two_factor_required'):
                logger.info("Two-factor authentication required")
                two_factor_identifier = login_json['two_factor_info']['two_factor_identifier']
                verification_code = input("Enter your 2FA code: ")
                two_factor_payload = {
                    'username': username,
                    'verificationCode': verification_code,
                    'identifier': two_factor_identifier,
                    'queryParams': '{}',
                }
                two_factor_response = self.ig_session.post('https://www.instagram.com/accounts/login/ajax/two_factor/', headers=login_headers, data=two_factor_payload)
                two_factor_response.raise_for_status()
                login_json = two_factor_response.json()
            if not login_json.get('authenticated'):
                logger.warning(f"AJAX login failed: {login_json}. Falling back to Selenium.")
                raise ValueError("AJAX login failed")
            logger.info("Login successful via AJAX")
            self.cookies = {cookie.name: cookie.value for cookie in self.ig_session.cookies}
        except (requests.RequestException, ValueError) as e:
            logger.error(f"AJAX login error: {e}. Attempting Selenium login.")

            # Fallback to Selenium login
            try:
                driver = self.init_driver()
                if self.instagram_login_selenium(driver, username, password):
                    cookies = driver.get_cookies()
                    for cookie in cookies:
                        self.ig_session.cookies.set(cookie['name'], cookie['value'])
                    logger.info("Selenium login successful")
                    self.cookies = {cookie.name: cookie.value for cookie in self.ig_session.cookies}
                    driver.quit()
                else:
                    driver.quit()
                    raise SystemExit("Selenium login failed")
            except Exception as e:
                logger.error(f"Selenium login error: {e}")
                raise SystemExit(f"Error in login: {e}")

        with open(cookies_path, 'wb') as f:
            pickle.dump(self.ig_session.cookies, f)
            logger.info(f"Saved cookies to {cookies_path}")

    def ig_cookies_exist(self, cookies_path: str) -> bool:
        if os.path.isfile(cookies_path):
            try:
                with open(cookies_path, 'rb') as f:
                    cookies = pickle.load(f)
                    self.ig_session.cookies.update(cookies)
                    # Verify cookies
                    response = self.ig_session.get('https://www.instagram.com/api/v1/users/web_profile_info/?username=instagram', headers=self.headers, proxies=self.proxies)
                    if response.status_code == 200:
                        self.cookies = {cookie.name: cookie.value for cookie in self.ig_session.cookies}
                        return True
                    logger.warning("Cookies invalid, will re-login")
            except Exception as e:
                logger.error(f"Error loading cookies: {e}")
        return False    
    def get_username_storyid(self, ig_url: str) -> tuple:
        """Extract username and story_id (if applicable) from URL."""
        profile_match = re.match(self.ig_profile_regex, ig_url)
        if profile_match:
            username = profile_match.group(1)
            story_id = '3446487468465775665'
            return username, story_id
        if '/s/' in ig_url:
            code = re.match(self.ig_highlights_regex, ig_url).group(1)
            try:
                decoded = base64.b64decode(code).decode().split(':')[1][:-1]
                return 'highlights', decoded
            except Exception as e:
                logger.error(f"Error decoding highlight URL: {e}")
                raise SystemExit('Error: Invalid highlight URL format.')
        story_match = re.match(self.ig_story_regex, ig_url)
        if story_match:
            username = story_match.group(1)
            story_id = story_match.group(2) or '3446487468465775665'
            return username, story_id
        raise SystemExit('Error: Invalid URL format. Please provide a profile, story, or highlight URL.')

    def get_userid_by_username(self, username: str, story_id: str) -> str:
        if username == 'highlights':
            return f'highlight:{story_id}'
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = self.headers.copy()
        max_retries = 3
        for attempt in range(max_retries):
            headers['x-csrftoken'] = self.get_csrf_token()
            try:
                time.sleep(random.uniform(1, 3))  # Add delay
                response = self.ig_session.get(url, headers=headers, proxies=self.proxies, allow_redirects=False)
                response.raise_for_status()
                data = response.json()
                if 'data' not in data or 'user' not in data['data'] or 'id' not in data['data']['user']:
                    raise ValueError("User ID not found in response")
                return data['data']['user']['id']
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if response.status_code == 429:
                    logger.info("Rate limit hit, waiting...")
                    time.sleep(10 * (2 ** attempt))
                    continue
                raise SystemExit(f"Error getting user ID: {e}")

    def get_ig_highlights(self, user_id: str) -> list:
        """Fetch highlight IDs for a user."""
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        highlights_endpoint = f'https://i.instagram.com/api/v1/highlights/{user_id}/highlights_tray/'
        try:
            response = self.ig_session.get(highlights_endpoint, headers=headers, proxies=self.proxies)
            response.raise_for_status()
            highlights_json = response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching highlights: {e}")
            raise SystemExit('Error getting highlights JSON')
        highlight_ids = []
        try:
            for highlight in highlights_json.get('tray', []):
                highlight_id = highlight.get('id', '').replace('highlight:', '')
                if highlight_id:
                    highlight_ids.append(highlight_id)
        except Exception as e:
            logger.error(f"Error parsing highlights: {e}")
            raise SystemExit(f"Error parsing highlights: {e}")
        return highlight_ids

    def read_existing_links(self, links_file: str, section: str) -> dict:
        """Read existing links from links.txt for a specific section with their statuses."""
        existing_links = {}
        if os.path.exists(links_file):
            try:
                with open(links_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    section_regex = rf'{section}:\n((?:https?://[^\n]+\s*(?:Success|Fail)?\n)*)'
                    section_match = re.search(section_regex, content)
                    if section_match:
                        lines = section_match.group(1).strip().split('\n')
                        for line in lines:
                            parts = line.strip().split()
                            if parts:
                                url = parts[0]
                                status = parts[1] if len(parts) > 1 else None
                                existing_links[url] = status
            except Exception as e:
                logger.error(f"Error reading {section} from {links_file}: {e}")
        return existing_links

    def save_links(self, highlight_links: list, post_links: list, reel_links: list, story_links: list, username: str, status_updates: dict = None) -> None:
        """Save all links to links.txt with their statuses."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        base_dir = os.path.join('downloaded_media', 'instagram', safe_username)
        os.makedirs(base_dir, exist_ok=True)
        links_file = os.path.join(base_dir, 'links.txt')
        status_updates = status_updates or {}

        # Read existing links with statuses
        existing_highlight_links = self.read_existing_links(links_file, 'Highlight Links')
        existing_post_links = self.read_existing_links(links_file, 'Post Links')
        existing_reel_links = self.read_existing_links(links_file, 'Reel Links')
        existing_story_links = self.read_existing_links(links_file, 'Story Links')

        # Merge new links with existing ones, preserving statuses
        all_highlight_links = {**existing_highlight_links, **{link: existing_highlight_links.get(link, None) for link in highlight_links}}
        all_post_links = {**existing_post_links, **{link: existing_post_links.get(link, None) for link in post_links}}
        all_reel_links = {**existing_reel_links, **{link: existing_reel_links.get(link, None) for link in reel_links}}
        all_story_links = {**existing_story_links, **{link: existing_story_links.get(link, None) for link in story_links}}

        # Apply status updates
        for link, status in status_updates.items():
            if link in all_highlight_links:
                all_highlight_links[link] = status
            elif link in all_post_links:
                all_post_links[link] = status
            elif link in all_reel_links:
                all_reel_links[link] = status
            elif link in all_story_links:
                all_story_links[link] = status

        # Write to links.txt
        try:
            with open(links_file, 'w', encoding='utf-8') as f:
                f.write("Highlight Links:\n")
                for link, status in sorted(all_highlight_links.items()):
                    f.write(f"{link} {status or ''}\n")
                f.write("\nPost Links:\n")
                for link, status in sorted(all_post_links.items()):
                    f.write(f"{link} {status or ''}\n")
                f.write("\nReel Links:\n")
                for link, status in sorted(all_reel_links.items()):
                    f.write(f"{link} {status or ''}\n")
                f.write("\nStory Links:\n")
                for link, status in sorted(all_story_links.items()):
                    f.write(f"{link} {status or ''}\n")
            logger.info(f"Saved links to {links_file} (Highlights: {len(all_highlight_links)}, Posts: {len(all_post_links)}, Reels: {len(all_reel_links)}, Stories: {len(all_story_links)})")
        except Exception as e:
            logger.error(f"Error saving links to {links_file}: {e}")

    def get_ig_stories_urls(self, user_id: str, fetch_highlights: bool = False, username: str = None) -> tuple:
        """Fetch story or highlight URLs and save highlight links to links.txt."""
        stories_urls = []
        thumbnail_urls = []
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        highlight_links = []

        if fetch_highlights:
            highlight_ids = self.get_ig_highlights(user_id)
            if not highlight_ids:
                logger.info(f"No highlights found for user_id: {user_id}")
                return stories_urls, thumbnail_urls, highlight_links

            for highlight_id in highlight_ids:
                highlight_endpoint = f'https://i.instagram.com/api/v1/feed/reels_media/?reel_ids=highlight:{highlight_id}'
                try:
                    response = self.ig_session.get(highlight_endpoint, headers=headers, proxies=self.proxies)
                    response.raise_for_status()
                    highlight_json = response.json()
                except requests.RequestException as e:
                    logger.error(f"Error fetching highlight {highlight_id}: {e}")
                    continue

                try:
                    reel = highlight_json.get('reels', {}).get(f'highlight:{highlight_id}', {})
                    items = reel.get('items', [])
                    for item in items:
                        if 'video_versions' in item:
                            url = item['video_versions'][0]['url']
                            stories_urls.append(url)
                            thumbnail_urls.append(item['image_versions2']['candidates'][0]['url'])
                        else:
                            url = item['image_versions2']['candidates'][0]['url']
                            stories_urls.append(url)
                            thumbnail_urls.append(url)
                        highlight_links.append(f"https://www.instagram.com/stories/highlights/{highlight_id}/")
                except Exception as e:
                    logger.error(f"Error parsing highlight {highlight_id}: {e}")
                    continue
        else:
            stories_endpoint = f'https://i.instagram.com/api/v1/feed/reels_media/?reel_ids={user_id}'
            try:
                response = self.ig_session.get(stories_endpoint, headers=headers, proxies=self.proxies)
                response.raise_for_status()
                stories_json = response.json()
            except requests.RequestException as e:
                logger.error(f"Error fetching stories: {e}")
                raise SystemExit('Error getting stories JSON')

            try:
                reel = stories_json.get('reels', {}).get(f'{user_id}', {})
                items = reel.get('items', [])
                if not items:
                    logger.info(f"No stories found for user_id: {user_id}")
                    return stories_urls, thumbnail_urls, highlight_links
                for item in items:
                    if 'video_versions' in item:
                        stories_urls.append(item['video_versions'][0]['url'])
                        thumbnail_urls.append(item['image_versions2']['candidates'][0]['url'])
                    else:
                        stories_urls.append(item['image_versions2']['candidates'][0]['url'])
                        thumbnail_urls.append(item['image_versions2']['candidates'][0]['url'])
            except Exception as e:
                logger.error(f"Error parsing stories: {e}")
                raise SystemExit(f"Error getting stories URLs: {e}")

        return stories_urls, thumbnail_urls, highlight_links

    def download(self, stories_urls_list: list, username: str) -> list:
        """Download stories or highlights to a local folder, skipping successes and updating statuses."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        base_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'highlights')
        os.makedirs(base_dir, exist_ok=True)
        links_file = os.path.join('downloaded_media', 'instagram', safe_username, 'links.txt')

        existing_links = self.read_existing_links(links_file, 'Highlight Links')
        downloaded_item_list = []
        status_updates = {}
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()

        for story_url in stories_urls_list:
            # Skip links marked as Success
            if story_url in existing_links and existing_links[story_url] == 'Success':
                logger.info(f"Skipping successful highlight: {story_url}")
                continue
            try:
                story_request = self.ig_session.get(story_url, headers=headers, proxies=self.proxies, stream=True)
                story_request.raise_for_status()
                filename = story_url.split('?')[0].split('/')[-1]
                path_filename = os.path.join(base_dir, filename)
                with open(path_filename, 'wb') as f:
                    for chunk in story_request.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            f.flush()
                downloaded_item_list.append(path_filename)
                status_updates[story_url] = 'Success'
                logger.info(f"Downloaded: {path_filename}")
            except Exception as e:
                status_updates[story_url] = 'Fail'
                logger.error(f"Error downloading or saving {story_url}: {e}")
                continue

        # Update links.txt with new statuses
        if status_updates:
            highlight_links = list(existing_links.keys()) + [url for url in stories_urls_list if url not in existing_links]
            self.save_links(highlight_links, [], [], [], username, status_updates)

        return downloaded_item_list

    def get_profile_picture_url(self, username: str) -> str:
        """Fetch the profile picture URL for a given username."""
        if username == 'highlights':
            logger.warning("Profile picture not available for highlights")
            return ""
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        try:
            response = self.ig_session.get(url, headers=headers, proxies=self.proxies)
            response.raise_for_status()
            data = response.json()
            if 'data' in data and 'user' in data['data'] and 'profile_pic_url_hd' in data['data']['user']:
                return data['data']['user']['profile_pic_url_hd']
            else:
                logger.error("Profile picture URL not found in response")
                return ""
        except requests.RequestException as e:
            logger.error(f"Error fetching profile picture URL: {e}")
            return ""
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing profile picture URL: {e}")
            return ""

    def download_avatar(self, username: str) -> str:
        """Download the profile picture (avatar) for a given username."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        base_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'avatar')
        os.makedirs(base_dir, exist_ok=True)
        profile_pic_url = self.get_profile_picture_url(username)
        if not profile_pic_url:
            logger.warning(f"No profile picture URL found for {username}")
            return ""
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        try:
            response = self.ig_session.get(profile_pic_url, headers=headers, proxies=self.proxies, stream=True)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error downloading avatar {profile_pic_url}: {e}")
            return ""
        filename = f"{safe_username}_avatar.jpg"
        path_filename = os.path.join(base_dir, filename)
        try:
            with open(path_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
            logger.info(f"Downloaded avatar: {path_filename}")
            return path_filename
        except Exception as e:
            logger.error(f"Error saving avatar {path_filename}: {e}")
            return ""

    def init_driver(self):
        """Initialize Selenium WebDriver (Edge)."""
        EDGE_DRIVER_PATH = r"driver\msedgedriver.exe"
        service = Service(executable_path=EDGE_DRIVER_PATH)
        options = webdriver.EdgeOptions()
        #--enable-unsafe-swiftshader
        # options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--headless")
        options.add_argument("--start-maximized")
        # options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # options.add_argument("--disable-webgl")  # Explicitly disable WebGL
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        options.add_argument(f"user-agent={random.choice(user_agents)}")
        try:
            driver = webdriver.Edge(service=service, options=options)
            return driver
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def instagram_login_selenium(self, driver, username, password):
        """Log in to Instagram using Selenium."""
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(username)
            password_field = driver.find_element(By.NAME, "password")
            password_field.send_keys(password)
            password_field.send_keys(Keys.ENTER)
            time.sleep(5)
            try:
                two_factor_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "verificationCode"))
                )
                two_factor_code = input("Enter your 2FA code: ")
                two_factor_field.send_keys(two_factor_code)
                two_factor_field.send_keys(Keys.ENTER)
                time.sleep(5)
            except TimeoutException:
                logger.info("No 2FA required or 2FA prompt not detected.")
            if "accounts/login" not in driver.current_url:
                logger.info("Selenium login successful!")
                return True
            else:
                logger.error("Selenium login failed. Please check credentials or network.")
                return False
        except Exception as e:
            logger.error(f"Selenium login error: {e}")
            return False

    def get_total_posts_selenium(self, driver, profile_url):
        """Get total posts using Selenium."""
        try:
            driver.get(profile_url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="x9f619"]'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            private_indicator = soup.select_one('h2:-soup-contains("This Account is Private")')
            if private_indicator:
                logger.error("Profile is private and cannot be accessed.")
                return 0
            posts_elem = soup.select_one('span:-soup-contains("bài viết")')
            if not posts_elem:
                logger.error("Could not find element containing 'bài viết'.")
                return 0
            count_elem = soup.select_one('span.html-span')
            if count_elem:
                posts_count = int(count_elem.text.replace(',', '').replace('.', ''))
                logger.info(f"Total posts found via Selenium: {posts_count}")
                return posts_count
            else:
                logger.error("Could not find post count within 'bài viết' element.")
                return 0
        except Exception as e:
            logger.error(f"Error getting total posts via Selenium: {e}")
            return 0

    def get_total_posts_graphql(self, username):
        """Get total posts using GraphQL."""
        variables = {"username": username}
        variables_encoded = urllib.parse.quote(json.dumps(variables))
        doc_id = "7304184042904686"
        graphql_url = f"https://www.instagram.com/graphql/query/?doc_id={doc_id}&variables={variables_encoded}"
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        try:
            response = self.ig_session.get(graphql_url, headers=headers, cookies=self.cookies, proxies=self.proxies)
            response.raise_for_status()
            data = response.json()
            if 'data' not in data or 'user' not in data['data']:
                logger.error("Invalid GraphQL response structure.")
                return 0
            posts_count = data['data']['user']['edge_owner_to_timeline_media']['count']
            logger.info(f"Total posts found via GraphQL: {posts_count}")
            return posts_count
        except requests.RequestException as e:
            logger.error(f"Error fetching GraphQL URL {graphql_url}: {e}")
            return 0
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing GraphQL JSON data: {e}")
            return 0
    
    def get_total_posts_combined(self, driver, profile_url):
        """Get total posts using Instagram API."""
        username = urllib.parse.urlparse(profile_url).path.strip("/").split("?")[0]
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.ig_session.get(url, headers=headers, cookies=self.cookies, proxies=self.proxies, allow_redirects=False)
                response.raise_for_status()
                data = response.json()
                if 'data' not in data or 'user' not in data['data'] or 'edge_owner_to_timeline_media' not in data['data']['user']:
                    logger.error(f"Unexpected response format: {data}")
                    raise ValueError("Post count not found in response")
                posts_count = data['data']['user']['edge_owner_to_timeline_media']['count']
                logger.info(f"Total posts found via API: {posts_count}")
                return posts_count
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if response.status_code == 401 and attempt < max_retries - 1:
                    logger.info("Received 401 Unauthorized, retrying after delay...")
                    time.sleep(2 ** attempt)
                    continue
                if response.status_code == 403:
                    logger.error(f"Profile '{username}' is private or access is restricted.")
                    return 0
            except (KeyError, ValueError) as e:
                logger.error(f"Parsing error: {e}")
            time.sleep(2 ** attempt)

        logger.warning("API failed to retrieve post count.")
        try:
            posts_count = int(input("Please enter the total number of posts manually (or 0 to skip): "))
            return posts_count
        except ValueError:
            logger.error("Invalid input. Assuming 0 posts.")
            return 0

    def get_graphql_query_url(self, post_url):
        """Convert post or reel URL to GraphQL query URL."""
        try:
            shortcode_match = re.search(r'/(p|reel)/([^/?]+)', post_url)
            if not shortcode_match:
                raise ValueError("Invalid Instagram post or reel URL")
            shortcode = shortcode_match.group(2)
            variables = {
                "shortcode": shortcode,
                "fetch_tagged_user_count": None,
                "hoisted_comment_id": None,
                "hoisted_reply_id": None
            }
            variables_encoded = urllib.parse.quote(json.dumps(variables))
            doc_id = "8845758582119845"
            graphql_url = f"https://www.instagram.com/graphql/query/?doc_id={doc_id}&variables={variables_encoded}"
            return graphql_url
        except Exception as e:
            logger.error(f"Error generating GraphQL URL for {post_url}: {e}")
            return None

    def get_instagram_media_links(self, url, max_retries=3):
        """Fetch media links from Instagram GraphQL."""
        headers = self.headers.copy()
        headers['x-csrftoken'] = self.get_csrf_token()
        for attempt in range(max_retries):
            try:
                response = self.ig_session.get(url, cookies=self.cookies, headers=headers, proxies=self.proxies, timeout=30)
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit (429) for {url}. Waiting before retry...")
                    time.sleep(2 ** attempt * 5)
                    continue
                if response.status_code == 401:
                    logger.error(f"Unauthorized (401) for {url}. Cookies may be invalid.")
                    return []
                response.raise_for_status()
                data = response.json()
                if 'data' not in data or 'xdt_shortcode_media' not in data['data']:
                    logger.error(f"Invalid GraphQL response for {url}: {data.get('message', 'No data')}")
                    return []
                media_data = data['data']['xdt_shortcode_media']
                download_links = []
                media_id = media_data['id']

                if media_data.get('is_private') or media_data.get('is_restricted'):
                    logger.warning(f"Media {media_id} is private or restricted")
                    return []

                if 'edge_sidecar_to_children' in media_data:
                    media_items = media_data['edge_sidecar_to_children']['edges']
                    for item in media_items:
                        node = item['node']
                        if node['is_video']:
                            video_url = node.get('video_url')
                            if video_url:
                                download_links.append({
                                    'type': 'video',
                                    'id': node['id'],
                                    'url': video_url,
                                    'filename': f"video_{node['id']}.mp4"
                                })
                        else:
                            display_resources = node.get('display_resources', [])
                            if display_resources:
                                highest_quality = max(display_resources, key=lambda x: x['config_width'])
                                photo_url = highest_quality['src']
                                download_links.append({
                                    'type': 'photo',
                                    'id': node['id'],
                                    'url': photo_url,
                                    'filename': f"photo_{node['id']}.jpg"
                                })
                else:
                    if media_data['is_video']:
                        video_url = media_data.get('video_url')
                        if video_url:
                            download_links.append({
                                'type': 'video',
                                'id': media_id,
                                'url': video_url,
                                'filename': f"video_{media_id}.mp4"
                            })
                    else:
                        display_resources = media_data.get('display_resources', [])
                        if display_resources:
                            highest_quality = max(display_resources, key=lambda x: x['config_width'])
                            photo_url = highest_quality['src']
                            download_links.append({
                                'type': 'photo',
                                'id': media_id,
                                'url': photo_url,
                                'filename': f"photo_{media_id}.jpg"
                            })

                return download_links
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} - Error fetching URL {url}: {e}")
                time.sleep(2 ** attempt * 2)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} - Error parsing JSON data for {url}: {e}")
                time.sleep(2 ** attempt * 2)
        logger.error(f"Failed to fetch media links for {url} after {max_retries} retries")
        return []

    def count_downloaded_reels(self, username):
        """Count downloaded reel files in the reels directory."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        reel_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'reels')
        if not os.path.exists(reel_dir):
            logger.info(f"No reels directory found at {reel_dir}")
            return 0
        reel_files = [f for f in os.listdir(reel_dir) if f.endswith('.mp4')]
        logger.info(f"Found {len(reel_files)} downloaded reel files in {reel_dir}")
        return len(reel_files)
    def verify_downloads(self, username):
        """Verify downloaded posts and reels against successful links in links.txt."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        links_file = os.path.join('downloaded_media', 'instagram', safe_username, 'links.txt')
        reel_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'reels')
        video_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'video')
        image_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'images')

        # Read links from links.txt
        existing_post_links = self.read_existing_links(links_file, 'Post Links')
        existing_reel_links = self.read_existing_links(links_file, 'Reel Links')
        
        # Count successful links
        successful_posts = sum(1 for status in existing_post_links.values() if status == 'Success')
        successful_reels = sum(1 for status in existing_reel_links.values() if status == 'Success')
        
        # Count downloaded files
        post_files = []
        if os.path.exists(video_dir):
            post_files.extend([f for f in os.listdir(video_dir) if f.endswith('.mp4')])
        if os.path.exists(image_dir):
            post_files.extend([f for f in os.listdir(image_dir) if f.endswith('.jpg')])
        downloaded_posts = len(post_files)
        
        reel_files = [f for f in os.listdir(reel_dir) if f.endswith('.mp4')] if os.path.exists(reel_dir) else []
        downloaded_reels = len(reel_files)
        
        # Identify missing or failed downloads
        missing_posts = []
        missing_reels = []
        for link, status in existing_post_links.items():
            if status == 'Success':
                shortcode = re.search(r'/(p)/([^/?]+)', link)
                if shortcode:
                    media_id = shortcode.group(2)  # Simplified; ideally, fetch actual media ID
                    expected_files = [
                        os.path.join(video_dir, f"SnapInsta_{media_id}.mp4"),
                        os.path.join(image_dir, f"SnapInsta_{media_id}.jpg")
                    ]
                    if not any(os.path.exists(f) for f in expected_files):
                        missing_posts.append(link)
        for link, status in existing_reel_links.items():
            if status == 'Success':
                shortcode = re.search(r'/(reel)/([^/?]+)', link)
                if shortcode:
                    media_id = shortcode.group(2)
                    expected_file = os.path.join(reel_dir, f"SnapInsta_{media_id}.mp4")
                    if not os.path.exists(expected_file):
                        missing_reels.append(link)
        
        logger.info(f"Verification: {successful_posts} successful post links, {downloaded_posts} post files")
        logger.info(f"Verification: {successful_reels} successful reel links, {downloaded_reels} reel files")
        
        if missing_posts:
            logger.warning(f"Missing post files for {len(missing_posts)} successful links: {missing_posts}")
        if missing_reels:
            logger.warning(f"Missing reel files for {len(missing_reels)} successful links: {missing_reels}")
        
        return {
            'posts': {
                'successful': successful_posts,
                'downloaded': downloaded_posts,
                'missing': missing_posts
            },
            'reels': {
                'successful': successful_reels,
                'downloaded': downloaded_reels,
                'missing': missing_reels
            }
        }
    def scrape_instagram_links(self, driver, url, max_retries=3, expected_posts=0, existing_links=None):
        """Scrape Instagram profile for highlight, post, and story links with mode-specific behavior."""
        existing_links = existing_links or []
        post_links = set(existing_links)
        start_count = len(post_links)
        links_file = os.path.join('downloaded_media', 'instagram', re.sub(r'[^\w\-_\. ]', '', urllib.parse.urlparse(url).path.strip("/").split("?")[0]), 'links.txt')
        
        for attempt in range(max_retries):
            try:
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="x9f619"]'))
                )
                last_height = driver.execute_script("return document.body.scrollHeight")
                max_scrolls = 2100
                scroll_count = 0
                previous_post_count = start_count
                links_since_last_check = []
                match_positions = []

                if start_count > 0 and not self.update_mode:
                    logger.info(f"Fast scrolling to reach {start_count} existing links")
                    posts_per_row = 3
                    rows_needed = (start_count // posts_per_row) + 1
                    pixels_per_row = 400
                    scroll_position = rows_needed * pixels_per_row
                    driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                    time.sleep(random.uniform(3, 5))
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    temp_post_links = ['https://www.instagram.com' + elem['href'] for elem in soup.select('a[href*="/p/"], a[href*="/reel/"]')]
                    post_links.update(temp_post_links)
                    logger.info(f"After fast scroll, found {len(post_links)}/{expected_posts} posts")

                while scroll_count < max_scrolls and (expected_posts == 0 or len(post_links) < expected_posts or self.update_mode):
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(random.uniform(6, 8))
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    temp_post_links = ['https://www.instagram.com' + elem['href'] for elem in soup.select('a[href*="/p/"], a[href*="/reel/"]')]
                    new_links = [link for link in temp_post_links if link not in post_links]
                    post_links.update(new_links)
                    
                    # Duplicate checking only in update_mode
                    if self.update_mode:
                        links_since_last_check.extend(new_links)
                        # Check for duplicates every 30 links in update mode
                        if len(links_since_last_check) >= 30:
                            section = 'Post Links' if '/p/' in url else 'Reel Links'
                            existing_section_links = self.read_existing_links(links_file, section)
                            matches = [link for link in links_since_last_check if link in existing_section_links]
                            match_positions.extend([len(post_links) - len(links_since_last_check) + i for i, link in enumerate(links_since_last_check) if link in matches])
                            
                            logger.info(f"Checked {len(links_since_last_check)} links, found {len(matches)} duplicates")
                            
                            if len(matches) >= 5:
                                are_initial_matches = all(pos < 10 for pos in match_positions[-len(matches):])
                                if not are_initial_matches:
                                    logger.info(f"Found {len(matches)} matching links not at start, stopping scrape")
                                    break
                            links_since_last_check = []
                    
                    logger.info(f"Scroll {scroll_count + 1}/{max_scrolls}: Page height {new_height}, Posts found: {len(post_links)}/{expected_posts if expected_posts > 0 else 'unknown'}")
                    if len(post_links) == previous_post_count and new_height == last_height:
                        for check in range(3):
                            logger.info(f"Verification check {check + 1}/3: Waiting 30 seconds to confirm no more posts")
                            time.sleep(30)
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            new_height = driver.execute_script("return document.body.scrollHeight")
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            temp_post_links = ['https://www.instagram.com' + elem['href'] for elem in soup.select('a[href*="/p/"], a[href*="/reel/"]')]
                            post_links.update(temp_post_links)
                            if len(post_links) > previous_post_count or new_height != last_height:
                                logger.info(f"New posts found during verification check {check + 1}, continuing scroll")
                                break
                        else:
                            logger.info("No more posts loaded after three verification checks, stopping scroll.")
                            break
                    last_height = new_height
                    previous_post_count = len(post_links)
                    scroll_count += 1

                highlight_links = ['https://www.instagram.com' + elem['href'] for elem in soup.select('a[href*="/stories/highlights/"]')]
                profile_name = urllib.parse.urlparse(url).path.strip("/").split("?")[0]
                story_links = [f"https://www.instagram.com/stories/{profile_name}/"] if soup.select('a[href*="/stories/"]') else []
                reel_links = [link for link in post_links if '/reel/' in link]
                post_links = [link for link in post_links if '/p/' in link]

                logger.info(f"Attempt {attempt + 1}/{max_retries}: Found {len(post_links)} post links, {len(reel_links)} reel links")
                return list(set(highlight_links)), list(post_links), list(set(reel_links)), list(set(story_links))
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(10)
        logger.error(f"Failed to scrape links after {max_retries} retries")
        return [], [], [], []

    def download_file(self, url, filepath, max_retries=3):
        """Download a file with retries."""
        if os.path.exists(filepath):
            logger.info(f"File already exists: {filepath}, skipping download")
            return True
        for attempt in range(max_retries):
            try:
                response = self.ig_session.get(url, headers=self.headers, cookies=self.cookies, proxies=self.proxies, stream=True, timeout=30)
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit (429) for {url}. Waiting before retry...")
                    time.sleep(2 ** attempt * 5)
                    continue
                response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"Downloaded: {filepath}")
                return True
            except requests.RequestException as e:
                logger.error(f"Download attempt {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(2 ** attempt * 2)
        logger.error(f"Failed to download {url} after {max_retries} retries.")
        return False

    def process_post(self, url, username, media_type="post", max_retries=3):
        """Process a single post or reel link, updating download status."""
        safe_username = re.sub(r'[^\w\-_\. ]', '', username)
        video_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'reels' if media_type == 'reel' else 'video')
        image_dir = os.path.join('downloaded_media', 'instagram', safe_username, 'reels' if media_type == 'reel' else 'images')
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)
        links_file = os.path.join('downloaded_media', 'instagram', safe_username, 'links.txt')

        # Skip if already marked as Success
        section = 'Reel Links' if media_type == 'reel' else 'Post Links'
        existing_links = self.read_existing_links(links_file, section)
        if url in existing_links and existing_links[url] == 'Success':
            logger.info(f"Skipping successful {media_type}: {url}")
            return

        status_updates = {}
        success = True
        for attempt in range(max_retries):
            try:
                graphql_url = self.get_graphql_query_url(url)
                if not graphql_url:
                    logger.error(f"Failed to generate GraphQL URL for {url}")
                    success = False
                    break
                time.sleep(random.uniform(2, 4))
                download_links = self.get_instagram_media_links(graphql_url)
                if not download_links:
                    logger.error(f"No media links found for {url}")
                    success = False
                    break
                for link in download_links:
                    try:
                        media_url = link['url']
                        media_type_item = link['type']
                        filename = f"SnapInsta_{link['id']}{'.mp4' if media_type_item == 'video' else '.jpg'}"
                        download_dir = video_dir if media_type_item == 'video' else image_dir
                        filepath = os.path.join(download_dir, filename)
                        if not self.download_file(media_url, filepath):
                            logger.error(f"Failed to download {media_url}")
                            success = False
                        time.sleep(random.uniform(1, 3))
                    except Exception as e:
                        logger.error(f"Error downloading media {link['id']} from {url}: {e}")
                        success = False
                        continue
                if success:
                    break
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                success = False
                time.sleep(5)

        status_updates[url] = 'Success' if success else 'Fail'
        logger.info(f"Processed {media_type} {url}: {status_updates[url]}")

        # Update links.txt with new status
        if status_updates:
            if media_type == 'reel':
                self.save_links([], [], [url], [], username, status_updates)
            else:
                self.save_links([], [url], [], [], username, status_updates)

def process_urls_file(scraper, driver, username, password, cookies_path, max_threads, update_mode):
    """Process URLs from urls.txt, updating statuses and handling successes/fails."""
    urls_file = os.path.join('downloaded_media', 'instagram', 'urls.txt')
    os.makedirs(os.path.dirname(urls_file), exist_ok=True)

    # Read URLs and their statuses
    url_statuses = {}
    if os.path.exists(urls_file):
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(maxsplit=1)
                    if parts:
                        url = parts[0]
                        status = parts[1] if len(parts) > 1 else None
                        url_statuses[url] = status
        except Exception as e:
            logger.error(f"Error reading {urls_file}: {e}")
            return

    # Process each URL
    for url in url_statuses:
        # Skip if already successful (no fails)
        if url_statuses[url] == 'Success':
            logger.info(f"Skipping successful URL: {url}")
            continue

        logger.info(f"Processing URL: {url}")
        try:
            # Set up profile processing
            scraper.set_proxies(os.getenv('HTTP_PROXY', ''), os.getenv('HTTPS_PROXY', ''))
            scraper.ig_login(username, password, cookies_path)
            parsed_url = urllib.parse.urlparse(url)
            profile_name = parsed_url.path.strip("/").split("?")[0]
            reels_url = f"https://www.instagram.com/{profile_name}/reels/"

            if not driver:
                driver = scraper.init_driver()
                if not scraper.instagram_login_selenium(driver, username, password):
                    logger.error("Selenium login failed.")
                    raise Exception("Selenium login failed")

            ig_username, story_id = scraper.get_username_storyid(url)
            logger.info(f"Extracted username: {ig_username}, story_id: {story_id}")
            user_id = scraper.get_userid_by_username(ig_username, story_id)
            logger.info(f"User ID: {user_id}")

            avatar_file = scraper.download_avatar(ig_username)
            if avatar_file:
                logger.info(f"Avatar downloaded: {avatar_file}")
            else:
                logger.warning("Failed to download avatar")

            expected_posts = scraper.get_total_posts_combined(driver, url) if not update_mode else 0
            links_file = os.path.join('downloaded_media', 'instagram', re.sub(r'[^\w\-_\. ]', '', ig_username), 'links.txt')
            existing_post_links = scraper.read_existing_links(links_file, 'Post Links')
            existing_reel_links = scraper.read_existing_links(links_file, 'Reel Links')
            existing_highlight_links = scraper.read_existing_links(links_file, 'Highlight Links')

            # Check if existing post links match expected_posts
            if not update_mode and len(existing_post_links) == expected_posts and expected_posts > 0:
                logger.info(f"Found {len(existing_post_links)} post links in links.txt, matching expected {expected_posts}. Skipping post scraping.")
                highlight_links, post_links, reel_links, story_links = list(existing_highlight_links.keys()), list(existing_post_links.keys()), list(existing_reel_links.keys()), []
            elif update_mode:
                logger.info("Update mode: Scraping for new posts and reels only")
                highlight_links, post_links, reel_links, story_links = scraper.scrape_instagram_links(
                    driver, url, expected_posts=0, existing_links=[]
                )
                # Filter out existing links
                post_links = [link for link in post_links if link not in existing_post_links]
                reel_links = [link for link in reel_links if link not in existing_reel_links]
            else:
                post_start_index = sum(1 for status in existing_post_links.values() if status != 'Success')
                logger.info(f"Default mode: Resuming post scraping from {post_start_index} of {expected_posts} expected posts")
                highlight_links, post_links, reel_links, story_links = scraper.scrape_instagram_links(
                    driver, url, expected_posts=expected_posts, existing_links=list(existing_post_links.keys())
                )

            stories_urls, thumbnail_urls, api_highlight_links = scraper.get_ig_stories_urls(user_id, fetch_highlights=True, username=ig_username)
            logger.info(f"Found {len(stories_urls)} highlight URLs via API")
            highlight_links.extend(api_highlight_links)

            scraper.save_links(highlight_links, post_links, reel_links, story_links, ig_username)
            downloaded_files = scraper.download(stories_urls, ig_username)
            logger.info(f"Downloaded highlight files: {downloaded_files}")

            # Process posts
            if update_mode:
                total_posts = len(post_links)
                post_links_to_download = post_links
            else:
                post_links_to_download = [
                    link for link in post_links
                    if link not in existing_post_links or existing_post_links[link] != 'Success'
                ]
                total_posts = len(post_links_to_download)
            
            if total_posts == 0:
                logger.info("No new or failed posts to download.")
            else:
                logger.info(f"Starting post download for {total_posts} posts with {max_threads} threads")
                with ThreadPoolExecutor(max_workers=max_threads) as executor:
                    future_to_link = {
                        executor.submit(scraper.process_post, link, ig_username, media_type="post"): link
                        for link in post_links_to_download
                    }
                    for future in as_completed(future_to_link):
                        link = future_to_link[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error processing post {link}: {e}")

            # Process reels
            downloaded_reels = scraper.count_downloaded_reels(ig_username)
            logger.info(f"Found {len(existing_post_links)} post links in links.txt and {downloaded_reels} downloaded reels")

            if not update_mode and len(existing_post_links) == expected_posts and expected_posts > 0:
                logger.info(f"All {expected_posts} posts already processed. Checking for new reels at {reels_url}")
                _, _, new_reel_links, _ = scraper.scrape_instagram_links(
                    driver, reels_url, expected_posts=0, existing_links=list(existing_reel_links.keys())
                )
                reel_links.extend(new_reel_links)
                total_reels = len(reel_links)
                reel_links_to_download = [
                    link for link in reel_links
                    if link not in existing_reel_links or existing_reel_links[link] != 'Success'
                ]
            elif update_mode:
                total_reels = len(reel_links)
                reel_links_to_download = reel_links
            else:
                logger.info(f"Scraping reels based on incomplete post links ({len(existing_post_links)}/{expected_posts})")
                _, _, new_reel_links, _ = scraper.scrape_instagram_links(
                    driver, reels_url, expected_posts=0, existing_links=list(existing_reel_links.keys())
                )
                reel_links.extend(new_reel_links)
                total_reels = len(reel_links)
                reel_links_to_download = [
                    link for link in reel_links
                    if link not in existing_reel_links or existing_reel_links[link] != 'Success'
                ]

            if total_reels == 0:
                logger.info("No reels to download.")
            else:
                logger.info(f"Starting reel download for {total_reels} reels with {max_threads} threads")
                scraper.save_links(highlight_links, post_links, reel_links, story_links, ig_username)
                with ThreadPoolExecutor(max_workers=max_threads) as executor:
                    future_to_link = {
                        executor.submit(scraper.process_post, link, ig_username, media_type="reel"): link
                        for link in reel_links_to_download
                    }
                    for future in as_completed(future_to_link):
                        link = future_to_link[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error processing reel {link}: {e}")

            # Verify downloads in default mode
            if not update_mode:
                verification = scraper.verify_downloads(ig_username)
                # Retry missing downloads
                missing_posts = verification['posts']['missing']
                missing_reels = verification['reels']['missing']
                if missing_posts:
                    logger.info(f"Retrying {len(missing_posts)} missing posts")
                    with ThreadPoolExecutor(max_workers=max_threads) as executor:
                        future_to_link = {
                            executor.submit(scraper.process_post, link, ig_username, media_type="post"): link
                            for link in missing_posts
                        }
                        for future in as_completed(future_to_link):
                            link = future_to_link[future]
                            try:
                                future.result()
                            except Exception as e:
                                logger.error(f"Error retrying post {link}: {e}")
                if missing_reels:
                    logger.info(f"Retrying {len(missing_reels)} missing reels")
                    with ThreadPoolExecutor(max_workers=max_threads) as executor:
                        future_to_link = {
                            executor.submit(scraper.process_post, link, ig_username, media_type="reel"): link
                            for link in missing_reels
                        }
                        for future in as_completed(future_to_link):
                            link = future_to_link[future]
                            try:
                                future.result()
                            except Exception as e:
                                logger.error(f"Error retrying reel {link}: {e}")

            # Check links.txt for status
            status, fail_counts = scraper.check_links_status(links_file)
            logger.info(f"Links status for {ig_username}: {status}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            status = f"{sum(fail_counts.values())} fail ({fail_counts['post']} post, {fail_counts['reel']} reels, {fail_counts['highlight']} highlight)" if 'fail_counts' in locals() else 'Fail'

        # Update urls.txt with the status
        url_statuses[url] = status
        try:
            with open(urls_file, 'w', encoding='utf-8') as f:
                for u, s in url_statuses.items():
                    f.write(f"{u} {s or ''}\n")
            logger.info(f"Updated {urls_file} with status for {url}: {status}")
        except Exception as e:
            logger.error(f"Error writing to {urls_file}: {e}")         
def check_links_status(self, links_file: str) -> tuple:
    """Check links.txt for status, excluding specific highlight links, and return status and fail counts."""
    highlight_exclude_pattern = r'https://www\.instagram\.com/stories/highlights/\d+/$'
    sections = ['Highlight Links', 'Post Links', 'Reel Links']
    fail_counts = {'post': 0, 'reel': 0, 'highlight': 0}
    all_success = True

    for section in sections:
        links = self.read_existing_links(links_file, section)
        section_type = 'highlight' if section == 'Highlight Links' else 'post' if section == 'Post Links' else 'reel'
        
        for url, status in links.items():
            # Skip highlight links matching the exclude pattern
            if section == 'Highlight Links' and re.match(highlight_exclude_pattern, url):
                continue
            # Count as fail if status is not 'Success' (including None or 'Fail')
            if status != 'Success':
                all_success = False
                fail_counts[section_type] += 1

    if all_success:
        return 'Success', fail_counts
    else:
        fail_summary = f"{sum(fail_counts.values())} fail ({fail_counts['post']} post, {fail_counts['reel']} reels, {fail_counts['highlight']} highlight)"
        return fail_summary, fail_counts
        
def main():
    load_dotenv()
    username = os.getenv('INSTAGRAM_USERNAME', 'vyhoang666')
    password = os.getenv('INSTAGRAM_PASSWORD', 'Armymenminh.1')
    cookies_path = 'ig_cookies'
    max_threads = 9
    update_mode = int(os.getenv('UPDATE_MODE', '0'))

    args = sys.argv[1:]
    if len(args) >= 6 and args[0] == '--username' and args[2] == '--password' and args[4] == '--url':
        username = args[1]
        password = args[3]
        update_mode = int(args[6]) if len(args) > 6 and args[6].isdigit() else 0
    elif not (username and password):
        logger.error("Error: Missing credentials. Try:\npython instagram_scraper.py --username your_username --password your_password")
        sys.exit(1)

    scraper = InstagramScraper(update_mode=update_mode)
    driver = None
    try:
        process_urls_file(scraper, driver, username, password, cookies_path, max_threads, update_mode)
        logger.info("Download process completed for all URLs")
    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        scraper.ig_session.close()
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {e}")

if __name__ == "__main__":
    main()