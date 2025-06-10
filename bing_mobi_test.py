from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import time
import traceback
import hashlib
import os
import json
import signal
import sys
import urllib.parse
import logging
import requests
from datetime import datetime
from pytrends.request import TrendReq
import string

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bing_search.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cấu hình
EDGE_DRIVER_PATH = r"driver\msedgedriver.exe"
MAX_SEARCHES = 30
MAX_RETRIES = 3
KEYWORD_CACHE_FILE = "keyword_cache.json"
HOT_KEYWORDS_FILE = "hot_keywords.json"
TIMEOUT = 8  # Timeout tối ưu cho tốc độ
TREND_PERIOD = "yearly"  # "daily", "weekly", "monthly", "yearly"
CHAR_ARRAY = list(string.ascii_lowercase + string.digits)  # Mảng ký tự cho từ khóa ngẫu nhiên

# Mảng từ khóa dự phòng
FALLBACK_KEYWORDS = [
    "trí tuệ nhân tạo", "học máy", "học sâu", "mạng nơ-ron", "xử lý ngôn ngữ tự nhiên",
    "thị giác máy tính", "học liên kết", "AI giải thích được", "AI tổng quát", "tự động hóa",
    "chatbot", "giọng nói nhân tạo", "phân tích dự đoán", "dữ liệu lớn", "phân tích dữ liệu",
    "điện toán đám mây", "điện toán biên", "điện toán lượng tử", "phần mềm mã nguồn mở",
    "DevOps", "low code", "no code", "phát triển phần mềm", "lập trình Python", "lập trình Java",
    "blockchain", "tiền điện tử", "an ninh mạng", "thực tế ảo", "thực tế tăng cường",
    "internet vạn vật", "robotics", "tự động hóa quy trình", "phân tích cảm xúc",
    "mạng 5G", "truyền thông không dây", "năng lượng tái tạo", "công nghệ xanh",
    "in 3D", "công nghệ nano", "công nghệ sinh học", "y học số", "genomics",
    "xe tự lái", "giao thông thông minh", "thành phố thông minh", "nông nghiệp thông minh",
    "fintech", "edtech", "healthtech", "proptech", "logistics thông minh"
]

driver = None

def signal_handler(sig, frame):
    """Xử lý tín hiệu Ctrl+C."""
    logging.info("🛑 Đã nhận tín hiệu hủy (Ctrl+C). Đang đóng trình duyệt...")
    if driver:
        try:
            driver.quit()
        except:
            pass
    logging.info("✅ Chương trình đã thoát.")
    sys.exit(0)

def load_keyword_cache():
    """Tải cache từ khóa đã sử dụng."""
    try:
        if os.path.exists(KEYWORD_CACHE_FILE):
            with open(KEYWORD_CACHE_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f).get('used_keywords', []))
        return set()
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi tải cache từ khóa: {e}")
        return set()

def save_keyword_cache(used_keywords):
    """Lưu cache từ khóa đã sử dụng."""
    try:
        with open(KEYWORD_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'used_keywords': list(used_keywords)}, f, ensure_ascii=False)
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi lưu cache từ khóa: {e}")

def generate_random_keyword():
    """Tạo từ khóa ngẫu nhiên từ mảng ký tự."""
    length = random.randint(5, 10)
    return ''.join(random.choice(CHAR_ARRAY) for _ in range(length))

def get_google_suggestions(query):
    """Lấy gợi ý tìm kiếm từ Google."""
    try:
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={urllib.parse.quote(query)}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        suggestions = response.json()[1]
        return [s for s in suggestions if s not in load_keyword_cache()][:10]
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi lấy gợi ý Google: {e}")
        return []

def get_hot_keywords(period="daily"):
    """Lấy từ khóa hot từ Google Trends theo kỳ."""
    cache_file = HOT_KEYWORDS_FILE
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Kiểm tra cache
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        if cache.get('date') == today and cache.get('period') == period and cache.get('keywords'):
            logging.info(f"📚 Sử dụng từ khóa hot từ cache ({period}).")
            return cache['keywords']
    
    max_retries = 3
    regions = ["vietnam", "united_states", None]
    
    for region in regions:
        for attempt in range(max_retries):
            try:
                logging.info(f"🌐 Đang lấy từ khóa hot từ Google Trends (khu vực: {region or 'toàn cầu'}, kỳ: {period}, lần {attempt + 1}/{max_retries})...")
                pytrends = TrendReq(hl="vi-VN", tz=420, retries=2, backoff_factor=0.2)
                
                # Lấy từ khóa theo kỳ
                if period == "daily":
                    trending_searches = pytrends.trending_searches(pn=region).head(50)[0].tolist()
                elif period == "weekly":
                    pytrends.build_payload(kw_list=["công nghệ"], timeframe='now 7-d', geo='VN')
                    trending_searches = pytrends.related_queries()['công nghệ']['top']['query'].tolist()
                elif period == "monthly":
                    pytrends.build_payload(kw_list=["công nghệ"], timeframe='now 30-d', geo='VN')
                    trending_searches = pytrends.related_queries()['công nghệ']['top']['query'].tolist()
                elif period == "yearly":
                    pytrends.build_payload(kw_list=["công nghệ"], timeframe='today 12-m', geo='VN')
                    trending_searches = pytrends.related_queries()['công nghệ']['top']['query'].tolist()
                else:
                    trending_searches = pytrends.trending_searches(pn=region).head(50)[0].tolist()
                
                if not trending_searches:
                    raise ValueError("Không lấy được từ khóa từ Google Trends.")
                
                # Lọc từ khóa đã sử dụng
                used_keywords = load_keyword_cache()
                trending_searches = [k for k in trending_searches if k not in used_keywords]
                
                cache = {"date": today, "period": period, "keywords": trending_searches}
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, ensure_ascii=False)
                logging.info(f"✅ Đã lấy và lưu {len(trending_searches)} từ khóa hot từ Google Trends ({period}).")
                return trending_searches
            except Exception as e:
                logging.error(f"⚠️ Lỗi khi lấy Google Trends (khu vực: {region or 'toàn cầu'}): {e}")
                time.sleep(random.uniform(2, 5))
    
    # Fallback: Lấy gợi ý từ Google
    logging.info("⚠️ Không lấy được từ Google Trends, thử lấy gợi ý Google...")
    suggestions = get_google_suggestions("công nghệ")
    if suggestions:
        cache = {"date": today, "period": period, "keywords": suggestions}
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        logging.info(f"✅ Đã lấy và lưu {len(suggestions)} từ khóa từ gợi ý Google.")
        return suggestions
    
    # Fallback: Sử dụng mảng dự phòng
    logging.warning("⚠️ Không lấy được từ khóa từ Google, sử dụng mảng dự phòng...")
    used_keywords = load_keyword_cache()
    fallback_keywords = [k for k in FALLBACK_KEYWORDS if k not in used_keywords]
    if fallback_keywords:
        cache = {"date": today, "period": period, "keywords": fallback_keywords}
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
        logging.info(f"✅ Đã sử dụng {len(fallback_keywords)} từ khóa từ mảng dự phòng.")
        return fallback_keywords
    
    # Fallback cuối: Từ khóa ngẫu nhiên
    logging.warning("⚠️ Hết từ khóa dự phòng, tạo từ khóa ngẫu nhiên...")
    random_keywords = [generate_random_keyword() for _ in range(50)]
    cache = {"date": today, "period": period, "keywords": random_keywords}
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    return random_keywords

def init_driver(headless=False):
    """Khởi tạo Edge driver."""
    logging.info("Đang khởi tạo Edge driver...")
    try:
        service = Service(EDGE_DRIVER_PATH)
        options = Options()
        mobile_emulation = {"deviceName": "iPhone X"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 EdgiOS/46.3.23 Mobile/15E148 Safari/605.1.15")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")  # Ổn định headless
        if headless:
            options.add_argument("--headless=new")  # Headless mới ổn định hơn
        driver = webdriver.Edge(service=service, options=options)
        driver.set_page_load_timeout(30)  # Timeout cho tải trang
        logging.info("✅ Edge driver khởi tạo thành công!")
        return driver
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi khởi tạo driver: {e}")
        return None

def tick_recaptcha_if_present(driver):
    """Kiểm tra và tick reCAPTCHA nếu có."""
    try:
        iframe = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]"))
        )
        driver.switch_to.frame(iframe)
        logging.info("🔍 Tìm thấy reCAPTCHA, đang tick...")
        checkbox = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
        )
        checkbox.click()
        logging.info("✅ Đã tick reCAPTCHA")
        driver.switch_to.default_content()
        time.sleep(1)
    except TimeoutException:
        logging.info("ℹ️ Không có reCAPTCHA trên trang này.")
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi xử lý reCAPTCHA: {e}")

def get_page_hash(driver):
    """Tính hash của trang hiện tại."""
    try:
        return hashlib.sha256(driver.page_source.encode()).hexdigest()
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi tính hash: {e}")
        return ""

def login_if_needed(driver):
    """Đăng nhập nếu cần."""
    try:
        driver.get("https://www.bing.com/rewards/panelflyout?partnerId=MemberCenterMobile")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "promo_card"))
        )
        try:
            login_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Sign in')]"))
            )
            login_button.click()
            logging.info("Đang đăng nhập...")
            email_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "i0116"))
            )
            email_field.send_keys("YOUR_EMAIL")  # Thay bằng email của bạn
            email_field.send_keys(Keys.ENTER)
            password_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "i0118"))
            )
            password_field.send_keys("YOUR_PASSWORD")  # Thay bằng mật khẩu của bạn
            password_field.send_keys(Keys.ENTER)
            WebDriverWait(driver, 15).until(
                EC.url_contains("rewards")
            )
            logging.info("✅ Đăng nhập thành công!")
        except TimeoutException:
            logging.info("ℹ️ Đã đăng nhập hoặc không cần đăng nhập.")
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi đăng nhập: {e}")

def check_search_completion(driver):
    """Kiểm tra xem tìm kiếm có hoàn tất không, với delay 5s để xem panelflyout."""
    try:
        driver.get("https://www.bing.com/rewards/panelflyout")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "promo_cont"))
        )
        logging.info("⏳ Đang tạm dừng 5 giây để xem trang panelflyout...")
        time.sleep(5)  # Delay 5s để bạn xem thành quả
        try:
            points = driver.find_element(By.XPATH, "//div[@class='daily_search_row']/span[2]").text
            logging.info(f"✅ Points hiện tại: {points}")
            return True
        except NoSuchElementException:
            logging.warning("⚠️ Không tìm thấy phần tử điểm số, thử kiểm tra trang chính...")
            # Fallback: Kiểm tra trang Bing chính
            driver.get("https://www.bing.com")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            logging.info("✅ Trang Bing tải thành công, giả định tìm kiếm hoàn tất.")
            return True
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi kiểm tra hoàn tất tìm kiếm: {e}")
        return False

def search_bing(driver, keyword):
    """Thực hiện tìm kiếm trên Bing."""
    logging.info(f"🔍 Đang thực hiện tìm kiếm: {keyword}")
    for attempt in range(MAX_RETRIES):
        try:
            driver.get("https://www.bing.com")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            tick_recaptcha_if_present(driver)
            search_box = driver.find_element(By.ID, "sb_form_q")
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            logging.info(f"✅ Đã nhập và tìm kiếm: {keyword}")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )
            # Tối ưu hóa tương tác với kết quả
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(random.uniform(0.5, 2))
            results = driver.find_elements(By.CSS_SELECTOR, "#b_results .b_algo h2 a")
            if results:
                random.choice(results[:3]).click()
                time.sleep(random.uniform(1, 3))
            else:
                logging.warning("⚠️ Không tìm thấy kết quả, vẫn tiếp tục...")
            logging.info("✅ Kết quả tìm kiếm đã tải và tương tác.")
            return check_search_completion(driver)
        except TimeoutException:
            logging.error(f"❌ Timeout khi tải trang hoặc kết quả (lần {attempt + 1}/{MAX_RETRIES}).")
        except Exception as e:
            logging.error(f"⚠️ Lỗi trong quá trình tìm kiếm (lần {attempt + 1}/{MAX_RETRIES}): {e}")
        time.sleep(random.uniform(1, 3))  # Giảm thời gian chờ giữa các lần thử
    logging.error(f"❌ Tìm kiếm {keyword} thất bại sau {MAX_RETRIES} lần.")
    return False

def main():
    global driver
    driver = init_driver(headless=False)  # Đặt True để chạy headless
    if not driver:
        logging.error("❌ Không thể khởi tạo driver, thoát chương trình.")
        return

    signal.signal(signal.SIGINT, signal_handler)

    try:
        login_if_needed(driver)
        used_keywords = load_keyword_cache()
        last_keyword_fetch_date = None
        keywords = []
        search_count = 0

        while search_count < MAX_SEARCHES:
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_keyword_fetch_date != current_date:
                keywords = get_hot_keywords(period=TREND_PERIOD)
                last_keyword_fetch_date = current_date
                logging.info(f"📋 Số từ khóa hot ({TREND_PERIOD}): {len(keywords)}")

            available_keywords = [k for k in keywords if k not in used_keywords]
            if not available_keywords:
                logging.warning("⚠️ Hết từ khóa hot, thử lấy lại từ khóa...")
                keywords = get_hot_keywords(period=TREND_PERIOD)
                available_keywords = [k for k in keywords if k not in used_keywords]
                if not available_keywords:
                    logging.warning("⚠️ Vẫn không có từ khóa, reset cache và thử lại...")
                    used_keywords.clear()
                    save_keyword_cache(used_keywords)
                    keywords = get_hot_keywords(period=TREND_PERIOD)
                    available_keywords = [k for k in keywords if k not in used_keywords]

            keyword = random.choice(available_keywords)
            used_keywords.add(keyword)
            save_keyword_cache(used_keywords)

            if search_bing(driver, keyword):
                search_count += 1
                logging.info(f"✅ Tìm kiếm {search_count}/{MAX_SEARCHES} hoàn tất.")
            else:
                logging.warning(f"⚠️ Tìm kiếm {keyword} không thành công, thử từ khóa khác.")

            current_hash = get_page_hash(driver)
            logging.info(f"🔖 Hash trang hiện tại: {current_hash[:16]}...")
            time.sleep(random.uniform(3, 7))  # Thời gian chờ giữa các tìm kiếm

    except Exception as e:
        logging.error(f"❌ Lỗi trong vòng lặp chính: {e}")
        traceback.print_exc()
    finally:
        logging.info("🛑 Kết thúc chương trình.")
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()