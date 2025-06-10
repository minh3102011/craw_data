# config.py

headers = {
    "Host": "sv.dut.udn.vn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "http://sv.dut.udn.vn",
    "Referer": "http://sv.dut.udn.vn/PageDangNhap.aspx",
    "X-Microsoftajax": "Delta=true",
    "Accept": "*/*",
    "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Ch-Ua-Mobile": "?0"
}

# Mẫu payload, sẽ được cập nhật động username/password
payload_template = {
    "_ctl0:MainContent:QLTH_btnLogin": r"Đăng+nhập"
}
