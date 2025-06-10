import requests
from bs4 import BeautifulSoup
import json


khoa_lop = input("Nhập khóa và lớp: ")
for i in range (1,601):
    kq = khoa_lop + str(i).zfill(3)
    print(kq)
    
    r = requests.get(f'https://kytucxa.vku.udn.vn/home/info/find-student?code={kq}')

    html_doc = r.text
    soup = BeautifulSoup(html_doc, 'html.parser')
    try:
        raw_data = soup.p.text

        student_info = {}
        for line in raw_data.strip().split('\n'):
            key, value = line.split(": ", 1)
            student_info[key.strip()] = value.strip()

        json_data =json.loads( json.dumps(student_info, ensure_ascii=False, indent=4))
        print(json_data["Họ và tên"])

    except:
        print("Không tìm thấy sinh viên")
        continue
    with open(f'sinh_vien {khoa_lop}.txt', 'a', encoding='utf-8') as f:
        f.write(f"{json_data['Mã sinh viên']}\n")
        f.write(f"{json_data['Họ và tên']}\n")
        f.write(f"{json_data['Giới tính']}\n")
        f.write("\n")
