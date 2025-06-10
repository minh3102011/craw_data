import requests
from bs4 import BeautifulSoup

# Khởi tạo session
session = requests.Session()

headers_common = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://sinhvien.ufl.udn.vn/DangNhap/Login",
    "Origin": "https://sinhvien.ufl.udn.vn",
}

# Bước 1: Đăng nhập
login_url = "https://sinhvien.ufl.udn.vn/DangNhap/SaveToken"
payload = {
    "Role": "0",
    "UserName": "417210054",
    "Password": "Eileo55."
}

resp_login = session.post(login_url, data=payload, headers=headers_common)

if not resp_login.ok:
    print("[-] Đăng nhập thất bại")
    exit()

print("[+] Đăng nhập thành công")
def get_input_value(soup, input_id):
    el = soup.find("input", {"id": input_id})
    if el:
        return el.get("value", "").strip() or "Thiếu"
    return "Thiếu"
def get_checkbox_status(soup, checkbox_id):
    el = soup.find("input", {"id": checkbox_id, "type": "checkbox"})
    if el and el.has_attr("checked"):
        return "Có"
    return "Không"
def get_select_value(soup, select_id):
    el = soup.find("select", {"id": select_id})
    if el:
        selected = el.find("option", selected=True)
        if selected:
            return selected.text.strip()
        return "Thiếu"
    return "Thiếu"

# Bước 2: Truy cập trang Thông tin sinh viên
session.get("https://sinhvien.ufl.udn.vn/SinhVien", headers=headers_common)
response_tt = session.get("https://sinhvien.ufl.udn.vn/SinhVien/ThongTinSinhVien", headers=headers_common)
soup = BeautifulSoup(response_tt.text, "html.parser")

# Hàm hỗ trợ lấy dữ liệu
def get_value(label):
    tag = soup.find("span", string=lambda t: t and label in t)
    if tag:
        input_tag = tag.find_next(["input", "select"])
        if input_tag.name == "input":
            return input_tag.get("value", "").strip()
        elif input_tag.name == "select":
            selected = input_tag.find("option", selected=True)
            return selected.text.strip() if selected else ""
    return ""

# Dữ liệu cần trích xuất
data = {
    "Mã sinh viên": get_value("Mã sinh viên"),
    "Họ và tên": get_value("Họ và tên"),
    "Ngày sinh": get_value("Ngày sinh"),
    "Giới tính": get_value("Giới tính"),
    "Số CCCD": get_value("Số CCCD"),
    "Nơi cấp CCCD": get_value("Nơi cấp CCCD"),
    "Ngày cấp CCCD": get_value("Ngày cấp CCCD"),
    "Quốc tịch": get_value("Quốc tịch"),
    "Dân tộc": get_value("Dân tộc"),
    "Tôn giáo": get_value("Tôn giáo"),
    "Hệ đào tạo": get_value("Hệ đào tạo"),
    "Chuyên ngành": get_value("Chuyên ngành"),
    "Khóa học": get_value("Khóa học"),
    "Khóa tuyển sinh": get_value("Khóa tuyển sinh"),
    "Số điện thoại chính": get_value("Số điện thoại chính"),
    "Số điện thoại phụ": get_value("Số điện thoại phụ"),
    "Email cá nhân": get_value("Email"),
    "Email sinh viên": get_value("Email sinh viên"),
    "Đoàn viên": get_value("Là đoàn viên"),
    "Đảng viên": get_value("Là Đảng viên"),
    "Ngày vào Đoàn": get_value("Ngày vào Đoàn/Đảng"),
    "Học lực lớp 12": get_value("Học lực lớp 12"),
    "Hạnh kiểm lớp 12": get_value("Hạnh kiểm lớp 12"),
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
#Thong tin khac
more_info = {
    "Tỉnh thành Lớp 10": get_select_value(soup, "IdTinhLop10"),
    "Mã số bhyt": get_input_value(soup, "Ma_so_bao_hiem"),
}

# Ghi ra file
filename = f"{data['Họ và tên']}/info.txt"
import os
os.makedirs(os.path.dirname(filename), exist_ok=True)

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
