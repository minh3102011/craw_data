# Mở và đọc file đầu vào
file = "netflix.com"
with open("net.txt", "r", encoding="utf-8") as infile:
    lines = infile.readlines()

# Lọc các dòng chứa 'due.udn.vn'
filtered_lines = [line.strip() for line in lines if file in line]

# Ghi kết quả ra file mới
with open(f"{file}.txt", "w", encoding="utf-8") as outfile:
    for line in filtered_lines:
        outfile.write(line + "\n")

print(f"Đã tìm thấy {len(filtered_lines)} dòng chứa '{file}' và lưu vào '{file}.txt'.")
