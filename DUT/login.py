import requests
from bs4 import BeautifulSoup
from config import headers, payload_template
import urllib.parse
import os
import time

# Function to read accounts from account.txt
def read_accounts(file_path="DUT.txt"):
    accounts = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    username, password = line.strip().split(":")
                    accounts.append({"username": username, "password": password})
        return accounts
    except FileNotFoundError:
        print(f"❌ File {file_path} not found.")
        return []
    except Exception as e:
        print(f"❌ Error reading accounts: {e}")
        return []

# Helper function to safely extract text from select elements
def safe_select_text(soup, select_id, default="N/A"):
    select = soup.find("select", {"id": select_id})
    if select:
        option = select.find("option", selected=True)
        return option.text.strip() if option else default
    return default

# Main login function with retry mechanism
def login_account(account, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            # Create session to keep cookies
            session = requests.Session()

            # Login URL
            url = "http://sv.dut.udn.vn/PageDangNhap.aspx"

            # Step 1: Get login page to retrieve __VIEWSTATE, etc.
            res_get = session.get(url, headers=headers, verify=False)
            soup = BeautifulSoup(res_get.text, "html.parser")

            # Find hidden inputs in the form
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})
            viewstategen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})

            # Step 2: Prepare payload from form
            payload = payload_template.copy()
            payload["__VIEWSTATE"] = viewstate["value"] if viewstate else ""
            payload["__VIEWSTATEGENERATOR"] = viewstategen["value"] if viewstategen else ""

            # Add account credentials
            payload["_ctl0:MainContent:DN_txtAcc"] = account["username"]
            payload["_ctl0:MainContent:DN_txtPass"] = account["password"]

            # Send POST request for login
            res_post = session.post(url, headers=headers, data=payload, verify=False)
            soup = BeautifulSoup(res_post.text, "html.parser")

            # Check result
            if "pageRedirect" in res_post.text:
                # Extract and decode redirect URL
                lines = res_post.text.split("|")
                if "pageRedirect" in lines:
                    idx = lines.index("pageRedirect")
                    redirect_url_encoded = lines[idx + 2]
                    redirect_url = urllib.parse.unquote(redirect_url_encoded)
                    print(f"🔁 Redirect to: {redirect_url}")

                    # Send GET request to fetch final content
                    full_url = urllib.parse.urljoin(url, redirect_url)
                    res_final = session.get(full_url, headers=headers, verify=False)
                    soup = BeautifulSoup(res_final.text, "html.parser")

                    # Extract student information
                    student_info = {
                        " - Mã sinh viên": payload["_ctl0:MainContent:DN_txtAcc"],
                        " - Họ và tên": soup.find('input', {'id': 'CN_txtHoTen'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtHoTen"}) else "N/A",
                        " - Lớp": soup.find('input', {'id': 'CN_txtLop'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtLop"}) else "N/A",
                        " - Chương trình 2": soup.find('input', {'id': 'MainContent_CN_txtCT2'}).get('value', '').strip() if soup.find("input", {"id": "MainContent_CN_txtCT2"}) else "N/A",
                        " - Ngày sinh": soup.find('input', {'id': 'CN_txtNgaySinh'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtNgaySinh"}) else "N/A",
                        " - Giới tính": soup.find('input', {'id': 'CN_txtGioiTinh'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtGioiTinh"}) else "N/A",
                        " - Quốc tịch": safe_select_text(soup, "CN_cboQuocTich"),
                        " - Nơi sinh": safe_select_text(soup, "CN_cboNoiSinh"),
                        " - Địa chỉ cư trú hiện nay": soup.find('input', {'id': 'CN_txtCuTru'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtCuTru"}) else "N/A",
                        " - Tỉnh/ Thành phố": safe_select_text(soup, "CN_cboTinhCTru"),
                        " - Quận/ Huyện": safe_select_text(soup, "CN_cboQuanCTru"),
                        " - Phường/ Xã": safe_select_text(soup, "CN_cboPhuongCTru"),
                        " - Là địa chỉ của": safe_select_text(soup, "CN_cboDCCua"),
                        " - Số CCCD": soup.find('input', {'id': 'CN_txtSoCCCD'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtSoCCCD"}) else "N/A",
                        " - Ngày cấp CCCD": soup.find('input', {'id': 'CN_txtNcCCCD'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtNcCCCD"}) else "N/A",
                        " - Tôn giáo": safe_select_text(soup, "CN_cboTonGiao"),
                        " - Dân tộc": safe_select_text(soup, "CN_cboDanToc"),
                        " - Mã bhyt": soup.find('input', {'id': 'CN_txtSoBHYT'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtSoBHYT"}) else "N/A",
                        " - Hiệu lực bhyt": soup.find('input', {'id': 'CN_txtHanBHYT'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtHanBHYT"}) else "N/A",
                        " - Tài khoản cá nhân": soup.find('input', {'id': 'CN_txtTKNHang'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtTKNHang"}) else " noisy/A",
                        " - Tại ngân hàng": soup.find('input', {'id': 'CN_txtNgHang'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtNgHang"}) else "N/A",
                        " - Ngành học": soup.find('input', {'id': 'MainContent_CN_txtNganh'}).get('value', '').strip() if soup.find("input", {"id": "MainContent_CN_txtNganh"}) else "N/A",
                        " - Chương trình đào tạo": soup.find('input', {'id': 'MainContent_CN_txtCTDT'}).get('value', '').strip() if soup.find("input", {"id": "MainContent_CN_txtCTDT"}) else "N/A",
                        " - Tài khoản office trường cấp": soup.find('input', {'id': 'CN_txtMail1'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtMail1"}) else "N/A",
                        " - Mật khẩu office trường cấp": soup.find('input', {'id': 'CN_txtMK365'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtMK365"}) else "N/A",
                        " - Số điện thoại": soup.find('input', {'id': 'CN_txtPhone'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtPhone"}) else "N/A",
                        " - Facebook": soup.find('input', {'id': 'CN_txtFace'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtFace"}) else "N/A",
                        " - Email": soup.find('input', {'id': 'CN_txtMail2'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtMail2"}) else "N/A",
                    }

                    # Extract family information
                    day = safe_select_text(soup, "CN_cboNSMe")
                    month = safe_select_text(soup, "CN_cboTSMe")
                    year = safe_select_text(soup, "CN_cboNamSMe")
                    ngay_sinh_me = f"{day}/{month}/{year}" if day != "N/A" and month != "N/A" and year != "N/A" else "N/A"
                    co_dai_hoc_me = "Có" if soup.find("input", {"id": "CN_cboCoDHMe", "checked": True}) else "Không"
                    khong_co_me = "Có" if soup.find("input", {"id": "CN_cboxKMe", "checked": True}) else "Không"

                    day_father = safe_select_text(soup, "CN_cboNSCha")
                    month_father = safe_select_text(soup, "CN_cboTSCha")
                    year_father = safe_select_text(soup, "CN_cboNamSCha")
                    ngay_sinh_cha = f"{day_father}/{month_father}/{year_father}" if day_father != "N/A" and month_father != "N/A" and year_father != "N/A" else "N/A"
                    co_dai_hoc_cha = "Có" if soup.find("input", {"id": "CN_cboCoDHCha", "checked": True}) else "Không"
                    khong_co_cha = "Có" if soup.find("input", {"id": "CN_cboxKCha", "checked": True}) else "Không"

                    family_info = {
                        "\nCha\n - Họ tên cha": soup.find('input', {'id': 'CN_txtCHTenCha'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtCHTenCha"}) else "N/A",
                        " - Ngày sinh cha": ngay_sinh_cha,
                        " - Cha có bằng ĐH/CĐ": co_dai_hoc_cha,
                        " - Không có cha": khong_co_cha,
                        "\nMẹ\n - Họ tên mẹ": soup.find('input', {'id': 'CN_txtCHTenMe'}).get('value', '').strip() if soup.find("input", {"id": "CN_txtCHTenMe"}) else "N/A",
                        " - Ngày sinh mẹ": ngay_sinh_me,
                        " - Mẹ có bằng ĐH/CĐ": co_dai_hoc_me,
                        " - Không có mẹ": khong_co_me,
                        "\n - Họ tên chủ hộ": soup.find("input", {"id": "CN_txtTenCH"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtTenCH"}) else "N/A",
                        " - Điện thoại chủ hộ": soup.find("input", {"id": "CN_txtPhoneCH"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtPhoneCH"}) else "N/A",
                        " - Ngày sinh chủ hộ": soup.find("input", {"id": "CN_txtCHNgaySinh"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtCHNgaySinh"}) else "N/A",
                        " - Mối quan hệ với chủ hộ": safe_select_text(soup, "CN_cboCHQuanHe"),
                        "\n - Số nhà, đường": soup.find("input", {"id": "CH_txtSoNha"}).get("value", "").strip() if soup.find("input", {"id": "CH_txtSoNha"}) else "N/A",
                        " - Tỉnh/Thành phố": safe_select_text(soup, "CN_cboCHTinh"),
                        " - Quận/Huyện": safe_select_text(soup, "CN_cboCHQuan"),
                        " - Xã/Phường": safe_select_text(soup, "CN_cboCHPhuong"),
                    }

                    # Extract emergency contact information
                    noti_info = {
                        " - Họ tên/ Quan hệ": soup.find("input", {"id": "CN_txtKCTen"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtKCTen"}) else "N/A",
                        " - Điện thoại": soup.find("input", {"id": "CN_txtKCPhone"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtKCPhone"}) else "N/A",
                        " - Địa chỉ": soup.find("input", {"id": "CN_txtKCSoNha"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtKCSoNha"}) else "N/A",
                        " - Tỉnh/Thành phố": safe_select_text(soup, "CN_cboKCTinh"),
                        " - Quận/Huyện": safe_select_text(soup, "CN_cboKCQuan"),
                        " - Xã/Phường": safe_select_text(soup, "CN_cboKCPhuong"),
                    }

                    # Extract post-graduation and address information
                    info_after_graduation = {
                        " - Họ tên/ Số nhà, đường": soup.find("input", {"id": "CN_txtTNNha"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtTNNha"}) else "N/A",
                        " - Tỉnh/Thành phố": safe_select_text(soup, "CN_cboTNTinh"),
                        " - Quận/Huyện": safe_select_text(soup, "CN_cboTNQuan"),
                        " - Xã/Phường": safe_select_text(soup, "CN_cboTNPhuong"),
                    }

                    address_receive = {
                        " - Họ tên/ Số nhà, đường": soup.find("input", {"id": "CN_txtTNNhaHS"}).get("value", "").strip() if soup.find("input", {"id": "CN_txtTNNhaHS"}) else "N/A",
                        " - Tỉnh/Thành phố": safe_select_text(soup, "CN_cboTNTinhHS"),
                        " - Quận/Huyện": safe_select_text(soup, "CN_cboTNQuanHS"),
                        " - Xã/Phường": safe_select_text(soup, "CN_cboTNPhuongHS"),
                    }

                    print(f"✅ Login successful for {account['username']}.")
                    print(f"🎯 Page title after login: {soup.title.string if soup.title else 'No title'}")

                    # Create directory for student
                    full_name = student_info[" - Họ và tên"].strip()
                    directory = f"data/{full_name}"
                    os.makedirs(directory, exist_ok=True)

                    # Save info to info.txt
                    info_file_path = f"{directory}/info.txt"
                    with open(info_file_path, "w", encoding="utf-8") as f:
                        f.write("\n### 🏠 Thông tin sinh viên\n")
                        for label, value in student_info.items():
                            f.write(f"{label}: {value}\n")
                        f.write("\n### 🏠 Thông tin Gia đình\n")
                        for label, value in family_info.items():
                            f.write(f"{label}: {value}\n")
                        f.write("\n### 🏠 Thông tin Liên lạc khẩn\n")
                        for label, value in noti_info.items():
                            f.write(f"{label}: {value}\n")
                        f.write("\n### 🏠 Thông tin Địa chỉ nhận hồ sơ\n")
                        for label, value in address_receive.items():
                            f.write(f"{label}: {value}\n")
                        f.write("\n### 🏠 Thông tin Địa chỉ sau tốt nghiệp\n")
                        for label, value in info_after_graduation.items():
                            f.write(f"{label}: {value}\n")

                    # (Optional) Save HTML for debugging
                    with open(f"{directory}/after_login.html", "w", encoding="utf-8") as f:
                        f.write(res_final.text)

                    return  # Success, exit function

                else:
                    print(f"❌ No pageRedirect found for {account['username']}.")
            else:
                print(f"❌ Login failed or no redirect for {account['username']}.")

        except Exception as e:
            print(f"❌ Error processing {account['username']} (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"⏳ Retrying in 1 second...")
                time.sleep(1)
            else:
                print(f"❌ Failed after {max_retries} attempts for {account['username']}. Skipping.")
                # Log failed account to a file
                with open("failed_accounts.txt", "a", encoding="utf-8") as f:
                    f.write(f"{account['username']}:{account['password']} - Error: {str(e)}\n")
                return

# Main execution
if __name__ == "__main__":
    accounts = read_accounts()
    if accounts:
        for account in accounts:
            print(f"🔍 Processing account: {account['username']}")
            login_account(account)
            time.sleep(0.5)  # 0.5-second delay between requests
    else:
        print("❌ No accounts to process.")