import uuid

# Hàm xử lý và xuất file
def process_and_export(input_file, output_file, username_file, password_file):
    # Danh sách để lưu dữ liệu
    full_lines = []
    usernames = []
    passwords = []

    # Đọc file input
    with open(input_file, "r", encoding="utf-8-sig") as file:
        lines = file.readlines()

    # Xử lý từng dòng
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Tách dòng bằng dấu :
        parts = line.split(":")
        if len(parts) < 3:
            print(f"Dòng không đúng định dạng: {line}")
            continue

        # Lấy url, username, password
        password = parts[-1]
        username = parts[-2]
        url = ":".join(parts[:-2])

        # Lưu dữ liệu
        full_lines.append(f"{url}:{username}:{password}")
        usernames.append(username)
        passwords.append(password)

    # Xuất file output.txt (url:username:password)
    with open(output_file, "w", encoding="utf-8") as file:
        for line in full_lines:
            file.write(line + "\n")

    # Xuất file usernames.txt
    with open(username_file, "w", encoding="utf-8") as file:
        for username in usernames:
            file.write(username + "\n")

    # Xuất file passwords.txt
    with open(password_file, "w", encoding="utf-8") as file:
        for password in passwords:
            file.write(password + "\n")

    print(f"Đã xuất file thành công:\n- {output_file}\n- {username_file}\n- {password_file}")

# Thực thi
input_file = "netflix.com.txt"
output_file = "output.txt"
username_file = "usernames.txt"
password_file = "passwords.txt"

process_and_export(input_file, output_file, username_file, password_file)
