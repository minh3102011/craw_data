import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import re
import os
from time import sleep

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize variables
raw_khoa_lop = input("Nhập khóa và lớp (e.g., 23NS, 23 IT.B, 23.ITB): ")
max_captcha_attempts = 20
max_retries = 3

# Chuẩn hóa: loại bỏ khoảng trắng và dấu chấm
normalized = re.sub(r'\s+|\.', '', raw_khoa_lop.strip().upper())

# Tách khóa và lớp
match = re.match(r'^(\d{2})([A-Z]+)$', normalized)
if not match:
    print("❌ Sai định dạng lớp. Vui lòng nhập đúng (ví dụ: 23NS, 23 IT.B, ...)")
    exit(1)

khoa, lop = match.groups()
base_dir = os.path.join("data", khoa, lop)
os.makedirs(base_dir, exist_ok=True)

# Biến để dùng kiểm tra về sau (vì trong all_info.txt chứa theo raw format)
khoa_lop = raw_khoa_lop.strip()

# Path for all_info.txt
all_info_path = os.path.join(base_dir, "all_info.txt")

# Check if all_info.txt exists
if not os.path.exists(all_info_path):
    print(f"❌ File {all_info_path} does not exist. Exiting.")
    exit(1)

# Read all_info.txt to extract student data and verify khoa_lop
students = []
try:
    with open(all_info_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Extract khoa_lop from header
        header = lines[0].strip()
        match = re.match(r"Danh sách Mã sinh viên và Số CMND \((.*?)\):", header)
        if not match or match.group(1) != khoa_lop:
            print(f"❌ Invalid or mismatched khoa_lop in {all_info_path}. Expected {khoa_lop}, found {match.group(1) if match else 'none'}. Exiting.")
            exit(1)
        
        # Parse student entries
        for line in lines[2:]:  # Skip header and separator
            if line.strip():
                match = re.match(r"Mã sinh viên: (.*?): Số CMND: (.*?): Họ và tên: (.*)", line.strip())
                if match:
                    ma_sv, so_cmnd, fullname = match.groups()
                    students.append({'ma_sv': ma_sv, 'so_cmnd': so_cmnd, 'fullname': fullname})
                else:
                    print(f"⚠️ Skipping invalid line in {all_info_path}: {line.strip()}")
except Exception as e:
    print(f"❌ Error reading {all_info_path}: {e}. Exiting.")
    exit(1)

if not students:
    print(f"❌ No valid student data found in {all_info_path}. Exiting.")
    exit(1)

# Login process with CAPTCHA retry
print("\nStarting login process...")
sdt = "0777432682"
cccd = "Armymenminh.1"

# Create session for persistent authentication
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

# Retry CAPTCHA and login up to 20 times
captcha_attempt = 0
login_success = False
while captcha_attempt < max_captcha_attempts:
    captcha_attempt += 1
    print(f"\nLogin attempt {captcha_attempt}/{max_captcha_attempts}")

    # Get login page
    url = "https://daotao.vku.udn.vn/phuhuynh"
    resp = session.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Get CSRF token
    try:
        token = soup.find("input", {"name": "_token"})["value"]
    except (AttributeError, KeyError):
        print(f"❌ Không tìm thấy CSRF token on attempt {captcha_attempt}")
        sleep(1)
        continue

    # Get CAPTCHA
    captcha_url = "https://daotao.vku.udn.vn/code"
    captcha_resp = session.get(captcha_url, headers=headers)
    img = Image.open(BytesIO(captcha_resp.content))

    # Process CAPTCHA image: convert to black and white + threshold
    img = img.convert("L")
    img = img.point(lambda x: 0 if x < 160 else 255, '1')

    # Use pytesseract with appropriate config
    config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    captcha_text = pytesseract.image_to_string(img, config=config).strip()[:6]
    print(f"🔍 CAPTCHA đã giải mã: {captcha_text}")

    # Submit login form
    data = {
        "_token": token,
        "sdt": sdt,
        "cccd": cccd,
        "capchar": captcha_text
    }
    post_resp = session.post(url, data=data, headers=headers)

    # Check login success
    expected_url = f"https://daotao.vku.udn.vn/phuhuynh/{sdt}"
    if post_resp.url == expected_url:
        print("✅ Đăng nhập thành công!")
        print(f"🔗 Link: {post_resp.url}")
        login_success = True
        break
    else:
        print(f"❌ Sai CAPTCHA hoặc thông tin đăng nhập on attempt {captcha_attempt}")
        print(f"URL hiện tại: {post_resp.url}")
        sleep(1)  # Wait before retrying

if not login_success:
    print(f"❌ Failed to log in after {max_captcha_attempts} CAPTCHA attempts. Exiting.")
    exit(1)

# Fetch detail pages for each student
print("\nFetching detail pages for students...")
for student in students:
    ma_sv = student['ma_sv']
    so_cmnd = student['so_cmnd']
    fullname = student['fullname']
    print(f"\nFetching details for student: {ma_sv} ({fullname})")

    # Construct detail URL
    detail_url = f"https://daotao.vku.udn.vn/phuhuynh/chitiet/{ma_sv}/{so_cmnd}"

    # Send GET request with session
    retry_count = 0
    while retry_count < max_retries:
        try:
            detail_resp = session.get(detail_url, headers=headers, timeout=10)
            detail_resp.raise_for_status()

            # Check if access was successful
            if detail_resp.status_code == 200 and "Chi tiết" in detail_resp.text:
                # Save HTML to score.html
                student_dir = os.path.join(base_dir, fullname)
                os.makedirs(student_dir, exist_ok=True)
                score_path = os.path.join(student_dir, "score.html")
                with open(score_path, 'w', encoding='utf-8') as f:
                    f.write(detail_resp.text)
                print(f"✅ Saved score.html for {ma_sv} in {student_dir}")

                # Detect and download profile image
                soup = BeautifulSoup(detail_resp.text, 'html.parser')
                img_tag = soup.find('div', class_='profile_pic').find('img', class_='img-circle profile_img') if soup.find('div', class_='profile_pic') else None
                if img_tag and 'src' in img_tag.attrs:
                    img_url = img_tag['src']
                    if img_url.startswith('http'):
                        try:
                            img_resp = session.get(img_url, headers=headers, timeout=10)
                            img_resp.raise_for_status()
                            img_path = os.path.join(student_dir, "profile_image.jpg")
                            with open(img_path, 'wb') as f:
                                f.write(img_resp.content)
                            print(f"✅ Downloaded profile_image.jpg for {ma_sv} from {img_url}")
                        except requests.RequestException as e:
                            print(f"⚠️ Failed to download profile image for {ma_sv}: {e}")
                    else:
                        print(f"⚠️ Invalid image URL for {ma_sv}: {img_url}")
                else:
                    print(f"⚠️ No profile image found for {ma_sv}")

                break
            else:
                raise ValueError("Response does not contain 'Chi tiết'")

        except (requests.RequestException, AttributeError, ValueError) as e:
            retry_count += 1
            print(f"Detail Error for {ma_sv} (Attempt {retry_count}/{max_retries}): {e}")
            if retry_count == max_retries:
                print(f"❌ Failed to fetch details for {ma_sv} after {max_retries} attempts, skipping")
                break
            sleep(1)

print("Processing completed.")