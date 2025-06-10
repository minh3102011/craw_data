# config.py

headers = {
    "Host": "due.udn.vn",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://due.udn.vn",
    "Referer": "https://due.udn.vn/",
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
    "ScriptManager": "dnn$ctr818$View$ctl00$UpdatePanel1|dnn$ctr818$View$ctl00$btnLogin",
    "StylesheetManager_TSSM": "",
    "ScriptManager_TSM": ";;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en:669ca791-a838-4419-82bc-9fa647338708:ea597d4b:b25378d2",
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__VIEWSTATEENCRYPTED": "",
    "dnn$ctr818$View$ctl00$ctl01$txtSearch": "",
    "__ASYNCPOST": "true",
    "dnn$ctr818$View$ctl00$btnLogin": "login"
}
