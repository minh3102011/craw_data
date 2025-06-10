import requests
from bs4 import BeautifulSoup
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open("usernames.txt", "r") as f:
    usernames = [line.strip() for line in f.readlines()]

with open("passwords.txt", "r") as f:
    passwords = [line.strip() for line in f.readlines()]
if len(usernames) != len(passwords):
    print("Số lượng username và password không khớp.")
    exit()

# Danh sách username và password


login_url = "https://elearning2.vku.udn.vn/login/index.php"

for i in range(len(usernames)):
    username = usernames[i]
    password = passwords[i]

    session = requests.Session()
    session.verify = False  # Bỏ qua cảnh báo SSL nếu có

    try:
        # Lấy logintoken
        resp = session.get(login_url)
        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "logintoken"})
        if not token_input:
            print(f"[{username}] ❌ Không tìm thấy logintoken.")
            continue
        logintoken = token_input.get("value")

        # Gửi POST request để đăng nhập
        payload = {
            "username": username,
            "password": password,
            "logintoken": logintoken
        }
        resp = session.post(login_url, data=payload, allow_redirects=True)

        # Kiểm tra nội dung phản hồi để xác định đăng nhập thành công
        if "https://elearning2.vku.udn.vn/my/" in resp.text:
            print(f"[{username}] ✅ Đăng nhập thành công")
            with open("success_logins.txt", "a") as f:
                f.write(f"{username}:{password}\n")
        else:
            print(f"[{username}] ❌ Đăng nhập thất bại")


    except Exception as e:
        print(f"[{username}] ⚠️ Lỗi: {e}")

    time.sleep(1)  # Chờ 1 giây giữa các lần login
