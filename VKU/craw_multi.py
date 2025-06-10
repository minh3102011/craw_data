import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from io import BytesIO
import re
import os
from time import sleep
import threading

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ========== INPUT VÀ TIỀN XỬ LÝ ==========
raw_khoa_lop = input("Nhập khóa và lớp (e.g., 23NS, 23 IT.B, 23.ITB): ")
normalized = re.sub(r'\s+|\.', '', raw_khoa_lop.strip().upper())
match = re.match(r'^(\d{2})([A-Z]+)$', normalized)

if not match:
    print("❌ Sai định dạng lớp. Vui lòng nhập đúng (ví dụ: 23NS, 23 IT.B, ...)")
    exit(1)

khoa, lop = match.groups()
base_dir = os.path.join("data", khoa, lop)
os.makedirs(base_dir, exist_ok=True)
khoa_lop = raw_khoa_lop.strip()
all_info_path = os.path.join(base_dir, "all_info.txt")

if not os.path.exists(all_info_path):
    print(f"❌ File {all_info_path} does not exist. Exiting.")
    exit(1)

# ========== ĐỌC DANH SÁCH SINH VIÊN ==========
students = []
try:
    with open(all_info_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        header = lines[0].strip()
        match = re.match(r"Danh sách Mã sinh viên và Số CMND \((.*?)\):", header)
        if not match or match.group(1) != khoa_lop:
            print(f"❌ Mismatch khoa_lop trong {all_info_path}. Expected: {khoa_lop}")
            exit(1)
        for line in lines[2:]:
            if line.strip():
                match = re.match(r"Mã sinh viên: (.*?): Số CMND: (.*?): Họ và tên: (.*)", line.strip())
                if match:
                    ma_sv, so_cmnd, fullname = match.groups()
                    students.append({'ma_sv': ma_sv, 'so_cmnd': so_cmnd, 'fullname': fullname})
                else:
                    print(f"⚠️ Skipping invalid line: {line.strip()}")
except Exception as e:
    print(f"❌ Error reading file: {e}")
    exit(1)

if not students:
    print("❌ No valid student data found.")
    exit(1)

# ========== ĐĂNG NHẬP ==========
print("\n🔐 Bắt đầu đăng nhập...")
sdt = "0777432682"
cccd = "Armymenminh.1"
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

max_captcha_attempts = 20
login_success = False

for attempt in range(1, max_captcha_attempts + 1):
    print(f"\nLogin attempt {attempt}/{max_captcha_attempts}")
    try:
        resp = session.get("https://daotao.vku.udn.vn/phuhuynh", headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]

        captcha_img = session.get("https://daotao.vku.udn.vn/code", headers=headers)
        img = Image.open(BytesIO(captcha_img.content)).convert("L")
        img = img.point(lambda x: 0 if x < 160 else 255, '1')
        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        captcha_text = pytesseract.image_to_string(img, config=config).strip()[:6]
        print(f"🔍 CAPTCHA: {captcha_text}")

        data = {"_token": token, "sdt": sdt, "cccd": cccd, "capchar": captcha_text}
        login = session.post("https://daotao.vku.udn.vn/phuhuynh", data=data, headers=headers)

        if login.url == f"https://daotao.vku.udn.vn/phuhuynh/{sdt}":
            print("✅ Đăng nhập thành công!")
            login_success = True
            break
        else:
            print("❌ CAPTCHA hoặc thông tin sai.")
        sleep(1)

    except Exception as e:
        print(f"⚠️ Lỗi trong quá trình đăng nhập: {e}")
        sleep(1)

if not login_success:
    print("❌ Không thể đăng nhập sau nhiều lần thử.")
    exit(1)

# ========== ĐỊNH NGHĨA HÀM LẤY THÔNG TIN ==========
max_retries = 3
def fetch_student_detail(student):
    ma_sv = student['ma_sv']
    so_cmnd = student['so_cmnd']
    fullname = student['fullname']
    print(f"\n📄 Fetching: {ma_sv} - {fullname}")

    detail_url = f"https://daotao.vku.udn.vn/phuhuynh/chitiet/{ma_sv}/{so_cmnd}"
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(detail_url, headers=headers, timeout=10)
            if resp.status_code == 200 and "Chi tiết" in resp.text:
                student_dir = os.path.join(base_dir, fullname)
                os.makedirs(student_dir, exist_ok=True)
                with open(os.path.join(student_dir, "score.html"), 'w', encoding='utf-8') as f:
                    f.write(resp.text)
                print(f"✅ Saved score.html for {ma_sv}")

                soup = BeautifulSoup(resp.text, 'html.parser')
                img_tag = soup.find('div', class_='profile_pic')
                if img_tag:
                    img = img_tag.find('img', class_='img-circle profile_img')
                    if img and 'src' in img.attrs:
                        img_url = img['src']
                        if img_url.startswith('http'):
                            try:
                                img_data = session.get(img_url, headers=headers, timeout=10)
                                with open(os.path.join(student_dir, "profile_image.jpg"), 'wb') as f:
                                    f.write(img_data.content)
                                print(f"📸 Image saved for {ma_sv}")
                            except:
                                print(f"⚠️ Failed to download image for {ma_sv}")
                break
            else:
                raise ValueError("No 'Chi tiết' found.")
        except Exception as e:
            print(f"❌ Attempt {attempt}/{max_retries} failed for {ma_sv}: {e}")
            sleep(1)

# ========== CHẠY ĐA LUỒNG ==========
print("\n🔄 Đang lấy thông tin sinh viên bằng đa luồng...\n")
threads = []
for student in students:
    t = threading.Thread(target=fetch_student_detail, args=(student,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("\n✅ Đã hoàn tất lấy thông tin tất cả sinh viên.")
print("📂 Tất cả thông tin đã được lưu trong thư mục:", base_dir)