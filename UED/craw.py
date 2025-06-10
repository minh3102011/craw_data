import requests
import base64
import os
import time
import traceback
import re
from pathlib import Path
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from config import NON_ESSENTIAL_HEADERS, COOKIES

# Function to read username-password pairs from ued.txt
def read_credentials(file_path="ued.txt"):
    credentials = []
    file_path = Path(file_path)  # Use pathlib for robust path handling
    print(f"Reading credentials from: {file_path.absolute()}")
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    username, password = line.split(":")
                    credentials.append({"username": username.strip(), "password": password.strip()})
    except FileNotFoundError:
        print(f"Error: {file_path} not found!")
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
    return credentials

# Function to sanitize filenames
def sanitize_filename(name):
    # Remove or replace invalid characters for filenames
    return re.sub(r'[<>:"/\\|?*]', '_', name.strip())

# Define URLs
base_url = "https://qlht.ued.udn.vn"
login_url = f"{base_url}/login/login"
dashboard_url = f"{base_url}/sinhvien"
thongtinsinhvien_url = f"{base_url}/sinhvien/thongtinsinhvien"
xemketquahoctap_url = f"{base_url}/sinhvien/diem/xemketquahoctap"

# Initialize headers as a dictionary
def initialize_headers():
    headers = {
        "Host": "qlht.ued.udn.vn",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Origin": base_url,
        "Referer": base_url + "/"
    }
    print(f"Initial headers: {headers}")
    
    # Debug and validate NON_ESSENTIAL_HEADERS
    print(f"Type of NON_ESSENTIAL_HEADERS: {type(NON_ESSENTIAL_HEADERS)}")
    print(f"NON_ESSENTIAL_HEADERS content: {NON_ESSENTIAL_HEADERS}")
    
    # Merge non-essential headers safely
    if isinstance(NON_ESSENTIAL_HEADERS, dict):
        headers.update(NON_ESSENTIAL_HEADERS)
        print(f"Headers after merging NON_ESSENTIAL_HEADERS: {headers}")
    else:
        print("Warning: NON_ESSENTIAL_HEADERS is not a dictionary. Using only essential headers.")
    
    return headers

# Get headers
headers = initialize_headers()
print(f"Global headers after initialization: {headers}")

# Read credentials from ued.txt
credentials = read_credentials()

# Process each account
for cred in credentials:
    username = cred["username"]
    password = cred["password"]
    print(f"\nProcessing account: {username}")

    max_attempts = 3
    attempt = 1
    success = False

    while attempt <= max_attempts and not success:
        print(f"Attempt {attempt} for {username}")
        # Create a new session for each attempt
        session = requests.Session()
        # Create a fresh copy of headers for each attempt
        session_headers = headers.copy()
        if not isinstance(session_headers, dict):
            print(f"Error: session_headers is not a dictionary at start: {type(session_headers)}")
            session_headers = initialize_headers()  # Reinitialize if invalid
        print(f"Session headers before login: {session_headers}")

        try:
            # Step 1: Send the POST request to log in
            payload = {
                "txt_Login_ten_dang_nhap": username,
                "pw_Login_mat_khau": password,
                "bt_Login_submit": "",
                "sskey": "1747026040"
            }
            response = session.post(login_url, headers=session_headers, data=payload, cookies=COOKIES, timeout=10)
            time.sleep(0.5)  # Delay after login request

            # Step 2: Check the response for the auto-submit form
            soup = BeautifulSoup(response.text, "html.parser")
            redirect_form = soup.find("form", {"name": "frmRedirect"})

            if redirect_form and redirect_form.get("action") == dashboard_url:
                print("Login successful, auto-submit form detected!")

                # Step 3: Extract redirect form fields and follow the redirect
                try:
                    redirect_payload = {
                        "sskey": redirect_form.find("input", {"name": "sskey"})["value"],
                        "h_Sys_Arr": redirect_form.find("input", {"name": "h_Sys_Arr"})["value"]
                    }
                except TypeError as e:
                    print(f"Error extracting redirect form fields for {username}: {str(e)}")
                    attempt += 1
                    continue

                dashboard_response = session.post(dashboard_url, headers=session_headers, data=redirect_payload, cookies=COOKIES, timeout=10)
                time.sleep(0.5)  # Delay after dashboard request

                # Step 4: Navigate to thongtinsinhvien page
                if dashboard_response.status_code == 200 and "sinhvien" in dashboard_response.url:
                    print("Dashboard accessed, navigating to thongtinsinhvien...")
                    print(f"Session headers before updating Referer: {session_headers}")

                    # Update Referer for thongtinsinhvien request
                    if not isinstance(session_headers, dict):
                        print(f"Error: session_headers is not a dictionary before updating Referer: {type(session_headers)}")
                        session_headers = initialize_headers()  # Reinitialize if invalid
                    session_headers["Referer"] = dashboard_url
                    print(f"Session headers after updating Referer: {session_headers}")

                    thongtinsinhvien_response = session.get(thongtinsinhvien_url, headers=session_headers, cookies=COOKIES, timeout=10)
                    time.sleep(0.5)  # Delay after thongtinsinhvien request

                    # Step 5: Check if thongtinsinhvien page loaded
                    if thongtinsinhvien_response.status_code == 200 and "thongtinsinhvien" in thongtinsinhvien_response.url:
                        print("thongtinsinhvien page accessed successfully!")
                        
                        # Parse the page
                        soup = BeautifulSoup(thongtinsinhvien_response.text, "html.parser")

                        # Extract student name
                        student_name_input = soup.find("input", {"id": "txt_Sua_ho_ten_sinh_vien"})
                        student_name = student_name_input["value"].strip() if student_name_input else username
                        print(f"Extracted student name: {student_name}")

                        # Sanitize student name for safe file paths
                        safe_student_name = sanitize_filename(student_name)

                        # Create output directory using pathlib
                        output_dir = Path("data") / safe_student_name
                        output_dir.mkdir(parents=True, exist_ok=True)
                        print(f"Output directory: {output_dir.absolute()}")

                        # Save HTML to info.html
                        info_html_path = output_dir / "info.html"
                        with info_html_path.open("w", encoding="utf-8") as f:
                            f.write(thongtinsinhvien_response.text)
                        print(f"HTML content saved to {info_html_path}")

                        # Extract student information from table
                        info_dict = {}
                        table = soup.find("table", {"id": "tb_Sua"})
                        if table:
                            print(f"Found table 'tb_Sua' for {username}. Parsing rows...")
                            for row_idx, row in enumerate(table.find_all("tr")):
                                cols = row.find_all("td")
                                print(f"Row {row_idx}: {len(cols)} columns - Content: {[col.text.strip()[:50] for col in cols]}")
                                # Skip rows with invalid structure
                                if len(cols) not in [2, 4] or not cols[0].text.strip():
                                    print(f"Skipping row {row_idx} for {username}: Invalid structure.")
                                    continue

                                try:
                                    if len(cols) == 2:
                                        # Single label-value pair
                                        label = cols[0].text.strip()
                                        value_cell = cols[1]
                                        
                                        # Handle input, select, textarea, or checkbox
                                        input_tag = value_cell.find("input")
                                        select_tag = value_cell.find("select")
                                        textarea_tag = value_cell.find("textarea")
                                        
                                        if input_tag and input_tag.get("type") == "checkbox":
                                            value = "Có" if input_tag.has_attr("checked") else "Không"
                                        elif input_tag and "value" in input_tag.attrs:
                                            value = input_tag["value"].strip()
                                        elif select_tag:
                                            selected_option = select_tag.find("option", selected=True)
                                            value = selected_option.text.strip() if selected_option else ""
                                        elif textarea_tag:
                                            value = textarea_tag.text.strip()
                                        else:
                                            value = value_cell.text.strip()  # Fallback to plain text
                                        info_dict[label] = value

                                    elif len(cols) == 4:
                                        # Two label-value pairs
                                        for i in [0, 2]:  # Process first and third <td> as labels
                                            try:
                                                label = cols[i].text.strip()
                                                value_cell = cols[i + 1]
                                                
                                                # Handle input, select, textarea, or checkbox
                                                input_tag = value_cell.find("input")
                                                select_tag = value_cell.find("select")
                                                textarea_tag = value_cell.find("textarea")
                                                
                                                if input_tag and input_tag.get("type") == "checkbox":
                                                    value = "Có" if input_tag.has_attr("checked") else "Không"
                                                elif input_tag and "value" in input_tag.attrs:
                                                    value = input_tag["value"].strip()
                                                elif select_tag:
                                                    selected_option = select_tag.find("option", selected=True)
                                                    value = selected_option.text.strip() if selected_option else ""
                                                elif textarea_tag:
                                                    value = textarea_tag.text.strip()
                                                else:
                                                    value = value_cell.text.strip()  # Fallback to plain text
                                                info_dict[label] = value
                                            except Exception as e:
                                                print(f"Error processing field {i//2+1} in row {row_idx} for {username}: {str(e)}")
                                                continue

                                    # Handle special case for Ngày sinh cha/mẹ (multiple selects)
                                    if len(cols) >= 4 and cols[0].text.strip() in ["Ngày sinh cha", "Ngày sinh mẹ"]:
                                        label = cols[0].text.strip()
                                        try:
                                            value_cell = cols[1]
                                            selects = value_cell.find_all("select")
                                            if len(selects) == 3:  # Day, Month, Year
                                                day = selects[0].find("option", selected=True)
                                                month = selects[1].find("option", selected=True)
                                                year = selects[2].find("option", selected=True)
                                                if day and month and year:
                                                    value = f"{day['value']}-{month['value']}-{year['value']}"
                                                    info_dict[label] = value
                                                else:
                                                    print(f"Skipping incomplete date field '{label}' in row {row_idx} for {username}")
                                        except Exception as e:
                                            print(f"Error processing date field '{label}' in row {row_idx} for {username}: {str(e)}")
                                            continue

                                except Exception as e:
                                    print(f"Error processing row {row_idx} for {username}: {str(e)}")
                                    continue
                        else:
                            print(f"Error: Table 'tb_Sua' not found for {username}. Saving HTML for inspection.")
                            error_html_path = Path("data") / f"{username}_error.html"
                            with error_html_path.open("w", encoding="utf-8") as f:
                                f.write(thongtinsinhvien_response.text)
                            print(f"Error HTML saved to {error_html_path}")

                        # Save thongtinsinhvien information to info.txt with formatted output
                        info_txt_path = output_dir / "info.txt"
                        with info_txt_path.open("w", encoding="utf-8") as f:
                            # Define sections for readability
                            sections = {
                                "Lý lịch": ["Mã sinh viên", "Họ tên sinh viên", "Giới tính", "Ngày sinh", "Mã lớp", "Tên đơn vị", "Tên chuyên ngành", "Tên hoạt động đào tạo", "Số CCCD", "Mã bảo hiểm xã hội", "Ngày cấp CCCD", "Nơi cấp CCCD", "Nơi sinh tỉnh/thành phố", "Nơi sinh quận/huyện", "Hộ khẩu tỉnh/thành phố", "Hộ khẩu quận/huyện", "Hộ khẩu phường/xã", "Tỉnh/thành phố quê quán", "Quận/huyện quê quán", "Phường/xã quê quán", "Quê quán", "Quốc gia", "Tôn giáo", "Dân tộc", "Ngày vào Đoàn", "Ngày vào Đảng", "Ngày vào hội sinh viên", "Ngoại ngữ chính", "Chức vụ lớp THPT", "Chức vụ đoàn THPT", "Chứng chỉ chính", "Ngân hàng", "Số tài khoản ngân hàng", "Số năm tham gia TNXP", "Số năm tham gia bộ đội", "Diện chính sách", "Năng khiếu", "Sở thích", "Ấn tượng khi nhập học", "Mong ước khi tốt nghiệp"],
                                "Tuyển sinh": ["Hệ phổ thông", "Diện đào tạo", "Ngành tuyển sinh", "Số báo danh", "Đối tượng", "Khu vực tuyển sinh", "Môn 1", "Môn 2", "Môn 3", "Điểm thưởng", "Điểm phạt", "Điểm tổng cộng", "Số văn bằng tốt nghiệp", "Chứng chỉ chính", "Ngày cấp bằng tốt nghiệp", "Nơi cấp bằng tốt nghiệp", "Mã trường/Đơn vị", "Điểm thi tốt nghiệp THPT", "Điểm trung bình lớp 10", "Môn điểm cao nhất lớp 10", "Điểm trung bình lớp 11", "Môn điểm cao nhất lớp 11", "Điểm trung bình lớp 12", "Môn điểm cao nhất lớp 12"],
                                "Liên lạc": ["Điện thoại cá nhân", "Email của trường", "Email cá nhân", "Địa chỉ liên lạc 1", "Địa chỉ liên lạc 2", "Người liên lạc", "Tỉnh/thành phố liên lạc"],
                                "Thông tin tạm trú": ["Hình thức tạm trú", "Tỉnh/thành phố tạm trú", "Ngày ngoại trú", "Quận/huyện tạm trú", "Địa chỉ tạm trú 1", "Địa chỉ tạm trú 2", "Điện thoại tạm trú", "Tên chủ hộ", "Phòng ký túc xá", "Dãy ký túc xá"],
                                "Gia đình": ["Tỉnh/TP gia đình", "Điện thoại gia đình", "Địa chỉ hộ khẩu 1", "Địa chỉ hộ khẩu 2", "Họ và tên cha", "Họ và tên mẹ", "Ngày sinh cha", "Ngày sinh mẹ", "Nghề nghiệp cha", "Nghề nghiệp mẹ", "Chỗ ở hiện nay cha", "Chỗ ở hiện nay mẹ", "Số anh em", "Con thứ mấy trong gia đình", "Số điện thoại cha", "Số điện thoại mẹ", "Số anh em học THPT", "Số anh em học Trung cấp", "Số anh em học Cao đẳng", "Số anh em học Đại học", "Thu nhập gia đình(VND)/Tháng", "Khó khăn của gia đình"],
                                "Hồ sơ": ["Mã hồ sơ", "Hồ sơ trúng tuyển", "Giấy báo trúng tuyển/nhập học", "Phiếu báo điểm", "Bằng tốt nghiệp", "Giấy tốt nghiệp tạm thời", "Giấy chứng nhận ưu tiên", "Giấy khai sinh", "Học bạ", "Nộp giấy đăng ký vắng mặt NVQS", "Bằng đại học", "Bằng cao đẳng/Trung cấp chuyên nghiệp"],
                                "Thông tin khác": ["Thông tin khen thưởng", "Thông tin nhận học bổng ngoài", "Thông tin nhận học bổng khuyến khích", "Thông tin kỷ luật", "Thông tin vi phạm", "Thông tin tham gia hoạt động"]
                            }

                            # Write formatted output
                            max_label_length = max(len(label) for label in info_dict.keys()) if info_dict else 30
                            for section, fields in sections.items():
                                f.write(f"\n{'=' * 50}\n{section}\n{'=' * 50}\n")
                                for field in fields:
                                    if field in info_dict:
                                        value = info_dict[field]
                                        f.write(f"{field:<{max_label_length}}: {value}\n")
                        
                        print(f"Student information saved to {info_txt_path}")

                        # Extract and save the image
                        img_tag = soup.find("img", src=lambda x: x and x.startswith("data:image"))
                        if img_tag:
                            try:
                                # Extract base64 data
                                img_data = img_tag["src"].split("base64,")[1].strip()
                                # Decode and save as image.jpg
                                image_path = output_dir / "image.jpg"
                                with image_path.open("wb") as f:
                                    f.write(base64.b64decode(img_data))
                                print(f"Image saved to {image_path}")
                            except Exception as e:
                                print(f"Failed to save image for {username}: {str(e)}")
                        else:
                            print(f"No base64 image found on the page for {username}!")
                            img_tags = soup.find_all("img")
                            print(f"Found {len(img_tags)} img tags: {[tag.get('src', '')[:50] for tag in img_tags]}")

                        # Step 6: Navigate to xemketquahoctap page
                        print("Navigating to xemketquahoctap...")
                        if not isinstance(session_headers, dict):
                            print(f"Error: session_headers is not a dictionary before xemketquahoctap: {type(session_headers)}")
                            session_headers = initialize_headers()
                        session_headers["Referer"] = thongtinsinhvien_url
                        ketquahoctap_response = session.get(xemketquahoctap_url, headers=session_headers, cookies=COOKIES, timeout=10)
                        time.sleep(0.5)  # Delay after xemketquahoctap request

                        # Step 7: Check if xemketquahoctap page loaded
                        if ketquahoctap_response.status_code == 200 and "xemketquahoctap" in ketquahoctap_response.url:
                            print("xemketquahoctap page accessed successfully!")
                            
                            # Save HTML to info_score.html
                            info_score_html_path = output_dir / "info_score.html"
                            with info_score_html_path.open("w", encoding="utf-8") as f:
                                f.write(ketquahoctap_response.text)
                            print(f"Academic HTML content saved to {info_score_html_path}")

                            # Parse the academic performance page
                            soup = BeautifulSoup(ketquahoctap_response.text, "html.parser")
                            academic_data = []
                            
                            # Find table(s) containing academic results
                            tables = soup.find_all("table")
                            for table in tables:
                                headers = [th.text.strip() for th in table.find_all("th")]
                                print(f"Academic table headers: {headers}")  # Debug headers
                                if headers:  # Only process tables with headers
                                    for row in table.find_all("tr")[1:]:  # Skip header row
                                        cols = row.find_all("td")
                                        if cols:
                                            try:
                                                row_data = {headers[i]: cols[i].text.strip() for i in range(min(len(headers), len(cols)))}
                                                academic_data.append(row_data)
                                            except Exception as e:
                                                print(f"Error processing academic row for {username}: {str(e)}")
                                                continue

                            # Save academic data to info_score.txt
                            info_score_txt_path = output_dir / "info_score.txt"
                            with info_score_txt_path.open("w", encoding="utf-8") as f:
                                f.write(f"{'=' * 50}\nKết quả học tập\n{'=' * 50}\n")
                                if academic_data:
                                    max_label_length = max(len(key) for row in academic_data for key in row.keys())
                                    for i, row in enumerate(academic_data, 1):
                                        f.write(f"Học kỳ {i}:\n")
                                        for key, value in row.items():
                                            f.write(f"  {key:<{max_label_length}}: {value}\n")
                                        f.write("\n")
                                else:
                                    f.write("No data available\n")
                            print(f"Academic data saved to {info_score_txt_path}")

                            success = True  # Mark as successful

                        else:
                            print(f"Failed to access xemketquahoctap for {username}. Status code: {ketquahoctap_response.status_code}")
                            print(f"Response URL: {ketquahoctap_response.url}")
                            attempt += 1

                    else:
                        print(f"Failed to access thongtinsinhvien for {username}. Status code: {thongtinsinhvien_response.status_code}")
                        print(f"Response URL: {thongtinsinhvien_response.url}")
                        attempt += 1

                else:
                    print(f"Failed to access dashboard for {username}. Status code: {dashboard_response.status_code}")
                    print(f"Response URL: {dashboard_response.url}")
                    attempt += 1

            else:
                print(f"Login failed for {username}. No redirect form found.")
                print(f"Response URL: {response.url}")
                attempt += 1

        except RequestException as e:
            print(f"Network error processing {username} on attempt {attempt}: {str(e)}")
            attempt += 1
        except Exception as e:
            print(f"Unexpected error processing {username} on attempt {attempt}: {str(e)}")
            traceback.print_exc()  # Print full traceback for debugging
            attempt += 1
        finally:
            session.close()  # Close session after each attempt

    if not success:
        print(f"Skipping {username} after {max_attempts} failed attempts.")