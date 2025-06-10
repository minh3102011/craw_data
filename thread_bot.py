from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
import os
import time
import requests
import urllib.parse
from pathlib import Path

# Get credentials from environment variables or use defaults
username = os.getenv('INSTAGRAM_USERNAME', 'INSTAGRAM_USERNAME')
password = os.getenv('INSTAGRAM_PASSWORD', 'INSTAGRAM_PASSWORD')

# Define the target username and download directories
target_username = 'zyvii_'
image_download_dir = f"downloaded_media/threads/{target_username}/images"
video_download_dir = f"downloaded_media/threads/{target_username}/videos"

# Set up Selenium WebDriver for Edge
EDGE_DRIVER_PATH = r"driver\msedgedriver.exe"
service = Service(executable_path=EDGE_DRIVER_PATH)
options = webdriver.EdgeOptions()
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Initialize the Edge driver
driver = webdriver.Edge(service=service, options=options)

def login_to_threads():
    try:
        driver.get('https://www.threads.com/login')
        time.sleep(2)
        
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
        )
        username_field.send_keys(username)
        
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="current-password"]'))
        )
        password_field.send_keys(password)
        
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.xwhw2v2.x1xdureb'))
        )
        login_button.click()
        
        WebDriverWait(driver, 20).until(
            EC.url_contains('threads.com')
        )
        time.sleep(20)
        if 'login' in driver.current_url:
            raise Exception("Login failed: Still on login page")
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        driver.save_screenshot('login_error.png')
        raise

def parse_srcset(srcset):
    try:
        entries = srcset.split(',')
        max_width = 0
        highest_quality_url = None
        for entry in entries:
            parts = entry.strip().split()
            if len(parts) != 2:
                continue
            url, width = parts
            width = int(width.rstrip('w'))
            if width > max_width:
                max_width = width
                highest_quality_url = url
        return highest_quality_url
    except Exception as e:
        print(f"Error parsing srcset: {e}")
        return None

def get_cookies_for_requests():
    selenium_cookies = driver.get_cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    return cookies

def download_file(url, file_path, file_type='image'):
    try:
        cookies = get_cookies_for_requests()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.threads.com/',
            'Accept': 'image/*,video/*',
            'Origin': 'https://www.threads.com'
        }
        response = requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=10)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Downloaded {file_type}: {file_path}")
            return True
        else:
            print(f"Failed to download {url}: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def scroll_and_collect_media(max_retries=3):
    image_urls = set()
    video_urls = set()
    processed_containers = set()  # Track processed media containers
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1}/{max_retries} to collect media.")
        driver.get(f'https://www.threads.com/@{target_username}/media')
        time.sleep(5)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print("Scrolled to bottom, waiting 20 seconds for content to load...")
            time.sleep(20)
            
            # Find media containers
            try:
                containers = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR,
                        'div.x1q6laf1.x123vp4x.x1joe5k6.xkr3pj5.x9f619.x6ikm8r.x10wlt62.x1n2onr6.x87ps6o.x5yr21d.xh8yej3'
                    ))
                )
                for container in containers:
                    try:
                        # Generate a unique identifier for the container (e.g., index or outerHTML hash)
                        container_id = id(container)
                        if container_id in processed_containers:
                            continue
                        
                        # Check for <img> element
                        img = container.find_elements(By.TAG_NAME, 'img')
                        if img:
                            img = img[0]
                            srcset = img.get_attribute('srcset')
                            if srcset and ('cdninstagram.com' in srcset or 'fbcdn.net' in srcset):
                                highest_quality_url = parse_srcset(srcset)
                                if highest_quality_url:
                                    image_urls.add(highest_quality_url)
                                    processed_containers.add(container_id)
                                    continue  # Skip video if image is found
                        
                        # Check for <video> element (only if no image)
                        video = container.find_elements(By.TAG_NAME, 'video')
                        if video:
                            video = video[0]
                            src = video.get_attribute('src')
                            if src and ('cdninstagram.com' in src or 'fbcdn.net' in src):
                                video_urls.add(src)
                                processed_containers.add(container_id)
                    except Exception as e:
                        print(f"Error processing container: {e}")
                        continue
            except Exception as e:
                print(f"Error finding media containers: {e}")
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more content to load.")
                break
            last_height = new_height
        
        print(f"Collected {len(image_urls)} unique image URLs and {len(video_urls)} unique video URLs in attempt {attempt + 1}.")
    
    return list(image_urls), list(video_urls)

def save_media(image_urls, video_urls):
    Path(image_download_dir).mkdir(parents=True, exist_ok=True)
    Path(video_download_dir).mkdir(parents=True, exist_ok=True)
    
    with open('media_urls.txt', 'w', encoding='utf-8') as f:
        f.write("Images:\n" + '\n'.join(image_urls) + "\nVideos:\n" + '\n'.join(video_urls))
    
    downloaded_image_count = 0
    for idx, url in enumerate(image_urls, 1):
        try:
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename += '.jpg'
            file_path = os.path.join(image_download_dir, f"image_{idx}_{filename}")
            
            if download_file(url, file_path, 'image'):
                downloaded_image_count += 1
            time.sleep(2)
        except Exception as e:
            print(f"Error processing image URL {url}: {e}")
            continue
    
    downloaded_video_count = 0
    for idx, url in enumerate(video_urls, 1):
        try:
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename.lower().endswith(('.mp4', '.mov')):
                filename += '.mp4'
            file_path = os.path.join(video_download_dir, f"video_{idx}_{filename}")
            
            if download_file(url, file_path, 'video'):
                downloaded_video_count += 1
            time.sleep(2)
        except Exception as e:
            print(f"Error processing video URL {url}: {e}")
            continue
    
    print(f"Successfully downloaded {downloaded_image_count} images to {image_download_dir}")
    print(f"Successfully downloaded {downloaded_video_count} videos to {video_download_dir}")

try:
    login_to_threads()
    image_urls, video_urls = scroll_and_collect_media(max_retries=3)
    save_media(image_urls, video_urls)

except Exception as e:
    print(f"An error occurred: {e}")
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

finally:
    driver.save_screenshot('debug.png')
    input("Press Enter to close the browser...")
    driver.quit()