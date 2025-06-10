import requests
from bs4 import BeautifulSoup
from config import headers, payload_template
import urllib3
import urllib.parse
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

retry_strategy = Retry(
    total=3,  # Max 3 retries
    backoff_factor=1,  # Wait 1s, 2s, 4s between retries
    status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
    allowed_methods=["GET", "POST"]  # Retry for GET and POST
)

# List of username:password pairs
credentials_file = "due.txt"  # Path to the input file
try:
    with open(credentials_file, "r", encoding="utf-8") as f:
        credentials = f.read().strip().splitlines()[1:]  # Skip header (Username:Password)
except FileNotFoundError:
    print(f"❌ Error: {credentials_file} not found")
    exit(1)
except Exception as e:
    print(f"❌ Error reading {credentials_file}: {str(e)}")
    exit(1)
# Parse credentials into list of (username, password) tuples
credentials_list = [line.split(":", 1) for line in credentials if line.strip()]


# Create session to keep cookies
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Login URL
url = "https://due.udn.vn/vi-vn/"

for username, password in credentials_list:
    print(f"\nProcessing account: {username}")
    try:
        # Step 1: Get login page to extract __VIEWSTATE, etc.
        res_get = session.get(url, headers=headers, verify=False)
        time.sleep(0.5)
        res_get.raise_for_status()
        soup = BeautifulSoup(res_get.text, "html.parser")

        # Find hidden inputs in the form
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        viewstategen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})

        # Step 2: Prepare payload from form
        payload = payload_template.copy()
        payload["__VIEWSTATE"] = viewstate["value"] if viewstate else ""
        payload["__VIEWSTATEGENERATOR"] = viewstategen["value"] if viewstategen else ""
        if eventvalidation:
            payload["__EVENTVALIDATION"] = eventvalidation["value"]

        # Add account details
        payload["dnn$ctr818$View$ctl00$username"] = username
        payload["dnn$ctr818$View$ctl00$password"] = password

        # Send POST request for login
        res_post = session.post(url, headers=headers, data=payload, verify=False)
        time.sleep(1)
        res_post.raise_for_status()
        soup = BeautifulSoup(res_post.text, "html.parser")

        # Check for pageRedirect
        if "pageRedirect" in res_post.text:
            # Extract and decode redirect URL
            lines = res_post.text.split("|")
            if "pageRedirect" in lines:
                idx = lines.index("pageRedirect")
                redirect_url_encoded = lines[idx + 2]
                redirect_url = urllib.parse.unquote(redirect_url_encoded)
                print(f"🔁 Redirect to: {redirect_url}")

                # Get the redirected page
                res_final = session.get(redirect_url, headers=headers, verify=False)
                time.sleep(0.5)
                res_final.raise_for_status()

                # Navigate to syllabus page
                syllabus_url = "https://due.udn.vn/vi-vn/syllsvcq"
                res_syllabus = session.get(syllabus_url, headers=headers, verify=False)
                time.sleep(0.5)
                res_syllabus.raise_for_status()
                soup_syllabus = BeautifulSoup(res_syllabus.text, "html.parser")

                # Extract student information for info.txt
                home_info = {
                    " - Hộ khẩu thường trú - Địa chỉ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHKTT_DiaChi"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHKTT_DiaChi"}) else "N/A",
                    " - Tỉnh/Thành phố": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHKTT_ThanhPho"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHKTT_ThanhPho"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHKTT_ThanhPho"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quận/Huyện": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Huyen"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Huyen"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Huyen"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Xã/Phường": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Xa"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Xa"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_combHKTT_Xa"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Thôn/Xóm": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHKTT_ThonXom"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHKTT_ThonXom"}) else "N/A"
                }
                home_info_2 = {
                    " - Địa chỉ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_DiaChi"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_DiaChi"}) else "N/A",
                    " - Tỉnh/Thành phố": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTTTV_ThanhPho"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTTTV_ThanhPho"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTTTV_ThanhPho"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quận/Huyện": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_QuanHuyen"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_QuanHuyen"}) else "N/A",
                    " - Xã/Phường": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_XaPhuong"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_XaPhuong"}) else "N/A",
                    " - Thôn/Xóm": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_ThonXom"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTTTV_ThonXom"}) else "N/A"
                }
                noti_school_info = {
                    " - Địa chỉ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_DIACHI"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_DIACHI"}) else "N/A",
                    " - Tỉnh/Thành phố": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropGUIGIAYBAO_TINH_THANHPHO"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropGUIGIAYBAO_TINH_THANHPHO"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropGUIGIAYBAO_TINH_THANHPHO"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quận/Huyện": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_QUANHUYEN"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_QUANHUYEN"}) else "N/A",
                    " - Xã/Phường": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_XA_PHUONG"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_XA_PHUONG"}) else "N/A",
                    " - Thôn/Xóm": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_THON_XOM"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtGUIGIAYBAO_THON_XOM"}) else "N/A"
                }
                student_info = {
                    " - Mã sinh viên": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMaSinhVien"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMaSinhVien"}) else "N/A",
                    " - Họ và tên": f"{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtHolot'}).get('value', '').strip()} {soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtTen'}).get('value', '').strip()}".strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHolot"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTen"}) else "N/A",
                    " - Ngày sinh": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgaysinh"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgaysinh"}) else "N/A",
                    " - Giới tính": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dopPhai"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dopPhai"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dopPhai"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Nơi sinh": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropNoisinh"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropNoisinh"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropNoisinh"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Email sinh viên": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEMAIL_SV"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEMAIL_SV"}) else "N/A",
                    " - Email Trường cấp": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail"}) else "N/A",
                    " - Mã số thẻ BHYT": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_MA_SO_THE"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_MA_SO_THE"}) else "N/A",
                    " - Nơi ĐK KCB BĐ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_NOI_DKY_KCB"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_NOI_DKY_KCB"}) else "N/A",
                    " - Mã khám chữa bệnh": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_MA_KHAM_CHUA_BENH"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_MA_KHAM_CHUA_BENH"}) else "N/A",
                    " - Giá trị sử dụng BHYT": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_GIA_TRI_SU_DUNG"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtBHYT_GIA_TRI_SU_DUNG"}) else "N/A",
                    " - Đơn vị công tác": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDonvicongtac"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDonvicongtac"}) else "N/A",
                    " - Chuyên ngành": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMajorName"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMajorName"}) else "N/A",
                    " - Lớp": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblClassID"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblClassID"}) else "N/A",
                    " - Di động": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiDD"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiDD"}) else "N/A",
                    " - Nhà riêng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiNR"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiNR"}) else "N/A",
                    " - Cơ quan": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiCQ"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDienthoaiCQ"}) else "N/A",
                    " - Khi cần báo tin cho": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtKhicanbaotincho"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtKhicanbaotincho"}) else "N/A",
                    " - Quốc tịch": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichSV"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichSV"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichSV"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Dân tộc": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantoc"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantoc"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantoc"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Tôn giáo": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTongiao"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTongiao"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropTongiao"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Tên trường THPT": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTHPT_TEN_TRUONG"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTHPT_TEN_TRUONG"}) else "N/A",
                    " - Địa chỉ trường THPT": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTHPT_DIA_CHI_TRUONG"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtTHPT_DIA_CHI_TRUONG"}) else "N/A",
                }
                paper_info = {
                    " - Số CMND": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCMND"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCMND"}) else "N/A",
                    " - Ngày cấp CMND": f"{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtNgayCap'}).get('value', '').strip()}/{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtThangCap'}).get('value', '').strip()}/{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtNamCap'}).get('value', '').strip()}" if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgayCap"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtThangCap"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNamCap"}) else "N/A",
                    " - Nơi cấp CMND": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNoicap"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNoicap"}) else "N/A",
                    "\n - Số CCCD": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtSoCCCD"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtSoCCCD"}) else "N/A",
                    " - Ngày cấp CCCD": f"{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtCCCD_NgayCap'}).get('value', '').strip()}/{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtCCCD_ThangCap'}).get('value', '').strip()}/{soup_syllabus.find('input', {'id': 'dnn_ctr11233_View_txtCCCD_NamCap'}).get('value', '').strip()}" if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCCCD_NgayCap"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCCCD_ThangCap"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCCCD_NamCap"}) else "N/A",
                    " - Nơi cấp CCCD": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCCCD_NoiCap"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtCCCD_NoiCap"}) else "N/A",
                    " - Năm tốt nghiệp": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNamtotnghiep"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNamtotnghiep"}) else "N/A",
                    " - Ngày ký bằng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgaykybang"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgaykybang"}) else "N/A",
                    " - Người ký bằng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNguoikybang"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNguoikybang"}) else "N/A",
                    " - Số hiệu bằng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtSohieubang"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtSohieubang"}) else "N/A",
                    " - Kiểm tra bằng tốt nghiệp": soup_syllabus.find("label", {"for": "dnn_ctr11233_View_radKiemtrabangTN_0"}).text.strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_radKiemtrabangTN_0"}) and soup_syllabus.find("input", {"id": "dnn_ctr11233_View_radKiemtrabangTN_0"}).get("checked") else "N/A"
                }
                family_info = {
                    "Cha\n - Họ và tên Cha": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenCha"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenCha"}) else "N/A",
                    " - Dân tộc Cha": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocCha"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocCha"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocCha"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quốc tịch Cha": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichCha"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichCha"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichCha"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Nghề nghiệp Cha": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNghenghiepCha"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNghenghiepCha"}) else "N/A",
                    " - Địa chỉ email Cha": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_Cha"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_Cha"}) else "N/A",
                    " - Hộ khẩu thường trú Cha": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruCha"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruCha"}) else "N/A",
                    " - Điện thoại Cha": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDIEN_THOAI_CHA"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDIEN_THOAI_CHA"}) else "N/A",
                    " - Học vấn Cha": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_CHA"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_CHA"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_CHA"}).find("option", {"selected": "selected"}) else "N/A",
                    "\nMẹ\n - Họ và tên Mẹ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenMe"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenMe"}) else "N/A",
                    " - Dân tộc Mẹ": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocMe"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocMe"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocMe"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quốc tịch Mẹ": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichMe"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichMe"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichMe"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Nghề nghiệp Mẹ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNghenghiepMe"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNghenghiepMe"}) else "N/A",
                    " - Địa chỉ email Mẹ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_Me"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_Me"}) else "N/A",
                    " - Hộ khẩu thường trú Mẹ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruMe"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruMe"}) else "N/A",
                    " - Điện thoại Mẹ": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDIEN_THOAI_ME"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtDIEN_THOAI_ME"}) else "N/A",
                    " - Học vấn Mẹ": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_ME"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_ME"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropHOC_VAN_ME"}).find("option", {"selected": "selected"}) else "N/A",
                    "\nVợ/Chồng\n - Họ và tên Vợ/Chồng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenVC"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHovatenVC"}) else "N/A",
                    " - Dân tộc Vợ/Chồng": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocVC"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocVC"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropDantocVC"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Quốc tịch Vợ/Chồng": soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichVC"}).find("option", {"selected": "selected"}).text.strip() if soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichVC"}) and soup_syllabus.find("select", {"id": "dnn_ctr11233_View_dropQuoctichVC"}).find("option", {"selected": "selected"}) else "N/A",
                    " - Nghề nghiệp Vợ/Chồng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgheNghepVC"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtNgheNghepVC"}) else "N/A",
                    " - Địa chỉ email Vợ/Chồng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_VC"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtEmail_VC"}) else "N/A",
                    " - Hộ khẩu thường trú Vợ/Chồng": soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruVC"}).get("value", "").strip() if soup_syllabus.find("input", {"id": "dnn_ctr11233_View_txtHokhauthuongtruVC"}) else "N/A"
                }
                cv_info = {
                    "Mã sinh viên": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMA_SINH_VIEN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblMA_SINH_VIEN"}) else "N/A",
                    "Họ tên": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN"}) else "N/A",
                    "Ngày sinh": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGAY_SINH"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGAY_SINH"}) else "N/A",
                    "Giới tính": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGIOI_TINH"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGIOI_TINH"}) else "N/A",
                    "Nơi sinh (tỉnh/TP)": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNOI_SINH_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNOI_SINH_SV"}) else "N/A",
                    "Quốc tịch": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblQUOC_TICH_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblQUOC_TICH_SV"}) else "N/A",
                    "Dân tộc": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDAN_TOC"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDAN_TOC"}) else "N/A",
                    "Tôn giáo": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTON_GIAO"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTON_GIAO"}) else "N/A",
                    "Số điện thoại SV": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_SV"}) else "N/A",
                    "Email": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_SV"}) else "N/A",
                    "Khi cần, báo tin cho số điện thoại": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblBAO_TIN_CHO_GDINH"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblBAO_TIN_CHO_GDINH"}) else "N/A",
                    "Chuyên ngành": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCHUYEN_NGANH"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCHUYEN_NGANH"}) else "N/A",
                    "Lớp": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblLOP"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblLOP"}) else "N/A",
                    "Số CMND": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_SO"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_SO"}) else "N/A",
                    "Ngày cấp CMND": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_NGAY_CAP"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_NGAY_CAP"}) else "N/A",
                    "Nơi cấp CMND": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_NOI_CAP"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCMND_NOI_CAP"}) else "N/A",
                    "Số CCCD": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_SO_IN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_SO_IN"}) else "N/A",
                    "Ngày cấp CCCD": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_NGAYCAP_IN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_NGAYCAP_IN"}) else "N/A",
                    "Nơi cấp CCCD": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_NOICAP_IN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblCCCD_NOICAP_IN"}) else "N/A",
                    "Hộ khẩu thường trú - Địa chỉ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_DIA_CHI_NHA_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_DIA_CHI_NHA_SV"}) else "N/A",
                    "Hộ khẩu thường trú - Tỉnh/Thành phố": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_THANH_PHO_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_THANH_PHO_SV"}) else "N/A",
                    "Hộ khẩu thường trú - Quận/Huyện": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_QUAN_HUYEN_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_QUAN_HUYEN_SV"}) else "N/A",
                    "Hộ khẩu thường trú - Xã/Phường": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_XA_PHUONG"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_XA_PHUONG"}) else "N/A",
                    "Hộ khẩu thường trú - Thôn/Xóm": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_THON_XOM"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHKTT_THON_XOM"}) else "N/A",
                    "Tạm trú - Tạm vắng - Địa chỉ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_DIA_CHI_NHA_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_DIA_CHI_NHA_SV"}) else "N/A",
                    "Tạm trú - Tạm vắng - Tỉnh/Thành phố": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_THANH_PHO_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_THANH_PHO_SV"}) else "N/A",
                    "Tạm trú - Tạm vắng - Quận/Huyện": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_QUAN_HUYEN_SV"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_QUAN_HUYEN_SV"}) else "N/A",
                    "Tạm trú - Tạm vắng - Xã/Phường": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_XA_PHUONG"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_XA_PHUONG"}) else "N/A",
                    "Tạm trú - Tạm vắng - Thôn/Xóm": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_THON_XOM"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblTTTV_THON_XOM"}) else "N/A",
                    "Địa chỉ gửi thông báo - Địa chỉ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_DIACHI"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_DIACHI"}) else "N/A",
                    "Địa chỉ gửi thông báo - Tỉnh/Thành phố": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_TINH_THANHPHO"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_TINH_THANHPHO"}) else "N/A",
                    "Địa chỉ gửi thông báo - Quận/Huyện": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_QUANHUYEN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_QUANHUYEN"}) else "N/A",
                    "Địa chỉ gửi thông báo - Xã/Phường": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_XA_PHUONG"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_XA_PHUONG"}) else "N/A",
                    "Địa chỉ gửi thông báo - Thôn/Xóm": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_THON_XOM"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblGUIGIAYBAO_THON_XOM"}) else "N/A",
                    "Họ tên Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN_CHA"}) else "N/A",
                    "Email Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_CHA"}) else "N/A",
                    "Số điện thoại Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_CHA"}) else "N/A",
                    "Nghề nghiệp Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGHE_NGHIEP_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGHE_NGHIEP_CHA"}) else "N/A",
                    "Hộ khẩu thường trú Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_KHAU_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_KHAU_CHA"}) else "N/A",
                    "Học vấn Cha": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHOC_VAN_CHA"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHOC_VAN_CHA"}) else "N/A",
                    "Họ tên Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_VA_TEN_ME"}) else "N/A",
                    "Email Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblEMAIL_ME"}) else "N/A",
                    "Số điện thoại Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblDIEN_THOAI_ME"}) else "N/A",
                    "Nghề nghiệp Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGHE_NGHIEP_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGHE_NGHIEP_ME"}) else "N/A",
                    "Hộ khẩu thường trú Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_KHAU_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHO_KHAU_ME"}) else "N/A",
                    "Học vấn Mẹ": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHOC_VAN_ME"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblHOC_VAN_ME"}) else "N/A",
                    "Ngày in": soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGAY_IN"}).text.strip() if soup_syllabus.find("span", {"id": "dnn_ctr11233_View_lblNGAY_IN"}) else "N/A"
                }

                # Create full name for directory
                full_name = student_info[" - Họ và tên"].strip()
                directory = f"data/{full_name}"
                os.makedirs(directory, exist_ok=True)

                # Save info to file
                info_file_path = f"{directory}/info.txt"
                with open(info_file_path, "w", encoding="utf-8") as f:
                    f.write("### 🏠 Thông tin sinh viên\n\n")
                    for label, value in student_info.items():
                        f.write(f"{label}: {value}\n")
                    
                    f.write("\n### 🏠 Thông tin giấy tờ\n\n")
                    for label, value in paper_info.items():
                        f.write(f"{label}: {value}\n")
                    
                    f.write("\n### 🏠 Thông tin thường trú\n\n")
                    for label, value in home_info.items():
                        f.write(f"{label}: {value}\n")
                        
                    f.write("\n### 🏠 Thông tin tạm trú\n\n")
                    for key, value in home_info_2.items():
                        f.write(f"{key}: {value}\n")

                    f.write("\n### 🏠 Thông tin nơi nhận thông báo\n\n")
                    for key, value in noti_school_info.items():
                        f.write(f"{key}: {value}\n")
                    
                    f.write("\n### 🏠 Thông tin gia đình\n\n")
                    for key, value in family_info.items():
                        f.write(f"{key}: {value}\n")
                
                cv_file_path = f"{directory}/cv.txt"
                with open(cv_file_path, "w", encoding="utf-8") as f:
                    f.write("ĐẠI HỌC ĐÀ NẴNG\n".center(80))
                    f.write("TRƯỜNG ĐẠI HỌC KINH TẾ\n".center(80))
                    f.write("-" * 40 + "\n".center(80))
                    f.write("SƠ YẾU LÝ LỊCH SINH VIÊN\n".center(80))
                    f.write("\n")
                    f.write("I. PHẦN BẢN THÂN SINH VIÊN\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{'Mã sinh viên':<30}: {cv_info['Mã sinh viên']}\n")
                    f.write(f"{'Họ tên':<30}: {cv_info['Họ tên']}\n")
                    f.write(f"{'Ngày sinh':<30}: {cv_info['Ngày sinh']}\n")
                    f.write(f"{'Giới tính':<30}: {cv_info['Giới tính']}\n")
                    f.write(f"{'Nơi sinh (tỉnh/TP)':<30}: {cv_info['Nơi sinh (tỉnh/TP)']}\n")
                    f.write(f"{'Quốc tịch':<30}: {cv_info['Quốc tịch']}\n")
                    f.write(f"{'Dân tộc':<30}: {cv_info['Dân tộc']}\n")
                    f.write(f"{'Tôn giáo':<30}: {cv_info['Tôn giáo']}\n")
                    f.write(f"{'Số điện thoại SV':<30}: {cv_info['Số điện thoại SV']}\n")
                    f.write(f"{'Email':<30}: {cv_info['Email']}\n")
                    f.write(f"{'Khi cần, báo tin cho số điện thoại':<30}: {cv_info['Khi cần, báo tin cho số điện thoại']}\n")
                    f.write(f"{'Chuyên ngành':<30}: {cv_info['Chuyên ngành']}\n")
                    f.write(f"{'Lớp':<30}: {cv_info['Lớp']}\n")
                    f.write(f"{'Số CMND':<30}: {cv_info['Số CMND']}\n")
                    f.write(f"{'Ngày cấp CMND':<30}: {cv_info['Ngày cấp CMND']}\n")
                    f.write(f"{'Nơi cấp CMND':<30}: {cv_info['Nơi cấp CMND']}\n")
                    f.write(f"{'Số CCCD':<30}: {cv_info['Số CCCD']}\n")
                    f.write(f"{'Ngày cấp CCCD':<30}: {cv_info['Ngày cấp CCCD']}\n")
                    f.write(f"{'Nơi cấp CCCD':<30}: {cv_info['Nơi cấp CCCD']}\n")
                    f.write("\nHỘ KHẨU THƯỜNG TRÚ\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{'Địa chỉ (số nhà, đường)':<30}: {cv_info['Hộ khẩu thường trú - Địa chỉ']}\n")
                    f.write(f"{'Tỉnh/Thành phố':<30}: {cv_info['Hộ khẩu thường trú - Tỉnh/Thành phố']}\n")
                    f.write(f"{'Quận/Huyện':<30}: {cv_info['Hộ khẩu thường trú - Quận/Huyện']}\n")
                    f.write(f"{'Xã/Phường':<30}: {cv_info['Hộ khẩu thường trú - Xã/Phường']}\n")
                    f.write(f"{'Thôn/Xóm':<30}: {cv_info['Hộ khẩu thường trú - Thôn/Xóm']}\n")
                    f.write("\nTẠM TRÚ - TẠM VẮNG\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{'Địa chỉ (số nhà, đường)':<30}: {cv_info['Tạm trú - Tạm vắng - Địa chỉ']}\n")
                    f.write(f"{'Tỉnh/Thành phố':<30}: {cv_info['Tạm trú - Tạm vắng - Tỉnh/Thành phố']}\n")
                    f.write(f"{'Quận/Huyện':<30}: {cv_info['Tạm trú - Tạm vắng - Quận/Huyện']}\n")
                    f.write(f"{'Xã/Phường':<30}: {cv_info['Tạm trú - Tạm vắng - Xã/Phường']}\n")
                    f.write(f"{'Thôn/Xóm':<30}: {cv_info['Tạm trú - Tạm vắng - Thôn/Xóm']}\n")
                    f.write("\nĐỊA CHỈ ĐỂ NHÀ TRƯỜNG GỬI THÔNG BÁO ĐẾN GIA ĐÌNH\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"{'Địa chỉ (số nhà, đường)':<30}: {cv_info['Địa chỉ gửi thông báo - Địa chỉ']}\n")
                    f.write(f"{'Tỉnh/Thành phố':<30}: {cv_info['Địa chỉ gửi thông báo - Tỉnh/Thành phố']}\n")
                    f.write(f"{'Quận/Huyện':<30}: {cv_info['Địa chỉ gửi thông báo - Quận/Huyện']}\n")
                    f.write(f"{'Xã/Phường':<30}: {cv_info['Địa chỉ gửi thông báo - Xã/Phường']}\n")
                    f.write(f"{'Thôn/Xóm':<30}: {cv_info['Địa chỉ gửi thông báo - Thôn/Xóm']}\n")
                    f.write("\nII. THÀNH PHẦN GIA ĐÌNH\n")
                    f.write("-" * 80 + "\n")
                    f.write("CHA\n")
                    f.write(f"{'Họ tên':<30}: {cv_info['Họ tên Cha']}\n")
                    f.write(f"{'Email':<30}: {cv_info['Email Cha']}\n")
                    f.write(f"{'Số điện thoại':<30}: {cv_info['Số điện thoại Cha']}\n")
                    f.write(f"{'Nghề nghiệp':<30}: {cv_info['Nghề nghiệp Cha']}\n")
                    f.write(f"{'Hộ khẩu thường trú':<30}: {cv_info['Hộ khẩu thường trú Cha']}\n")
                    f.write(f"{'Học vấn':<30}: {cv_info['Học vấn Cha']}\n")
                    f.write("\nMẸ\n")
                    f.write(f"{'Họ tên':<30}: {cv_info['Họ tên Mẹ']}\n")
                    f.write(f"{'Email':<30}: {cv_info['Email Mẹ']}\n")
                    f.write(f"{'Số điện thoại':<30}: {cv_info['Số điện thoại Mẹ']}\n")
                    f.write(f"{'Nghề nghiệp':<30}: {cv_info['Nghề nghiệp Mẹ']}\n")
                    f.write(f"{'Hộ khẩu thường trú':<30}: {cv_info['Hộ khẩu thường trú Mẹ']}\n")
                    f.write(f"{'Học vấn':<30}: {cv_info['Học vấn Mẹ']}\n")
                    f.write("\n")
                    f.write("Tôi xin cam đoan những lời khai trên là đúng sự thật. Tôi xin chịu trách nhiệm theo Quy chế hiện hành của Bộ Giáo dục và Đào tạo, của Trường về lời khai của tôi.\n")
                    f.write("\n")
                    f.write(f"{'Đà Nẵng,':<30} {cv_info['Ngày in']}\n")
                    f.write("Ký tên (ký và ghi rõ họ tên)\n")
                    f.write(f"{'':<30} {cv_info['Họ tên']}\n")

                # Save syllabus page
                print("📄 Syllabus page title:", soup_syllabus.title.string if soup_syllabus.title else "No title")
                with open(f"{directory}/syllabus_page.html", "w", encoding="utf-8") as f:
                    f.write(soup_syllabus.prettify())
                time.sleep(1)
                print("✅ Login successful.")
                print("🎯 Page title after login:", soup_syllabus.title.string if soup_syllabus.title else "No title")
                print(f"📝 Student info saved to: {info_file_path}")
                print(f"📝 CV info saved to: {cv_file_path}")
            else:
                print(f"❌ No pageRedirect found for {username}")
        else:
            print(f"❌ Login failed or no redirect for {username}")
    except Exception as e:
        print(f"❌ Error processing {username}: {str(e)}")
        continue

print("\n✅ Finished processing all accounts.")