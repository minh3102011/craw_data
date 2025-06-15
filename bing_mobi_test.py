from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import time
import traceback
import hashlib
import os
import json
import signal
import sys
import urllib.parse
import logging
from datetime import datetime, timedelta
from pytrends.request import TrendReq

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bing_search.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Cấu hình
EDGE_DRIVER_PATH = r"driver\msedgedriver.exe"
MAX_RETRIES = 3
KEYWORD_CACHE_FILE = "keyword_cache_default.json"
HOT_KEYWORDS_FILE = "hot_keywords.json"
KEYWORD_CACHE_DAYS = 1  # From first code
TIMEOUT = 8
TREND_PERIOD = "yearly"  # "daily", "weekly", "monthly", "yearly"
SEARCH_INTERVAL = 300  # 5 minutes in seconds

# Mảng từ khóa dự phòng
FALLBACK_KEYWORDS = ['trí tuệ nhân tạo', 'học máy', 'học sâu', 'mạng nơ-ron', 'xử lý ngôn ngữ tự nhiên', 'thị giác máy tính', 'học liên kết', 'AI giải thích được', 'AI tổng quát', 'tự động hóa siêu tốc', 'chatbot', 'giọng nói nhân tạo', 'phân tích dự đoán', 'dữ liệu lớn', 'phân tích dữ liệu', 'điện toán đám mây', 'điện toán biên', 'điện toán lượng tử', 'phần mềm mã nguồn mở', 'DevOps', 'low code', 'no code', 'phát triển phần mềm', 'lập trình Python', 'lập trình Java', 'lập trình JavaScript', 'công nghệ API', 'microservices', 'containerization', 'Kubernetes', 'Docker', 'CI/CD', 'serverless computing', 'cơ sở dữ liệu phân tán', 'hệ thống nhúng', 'IoT công nghiệp', 'cảm biến thông minh', 'robot công nghiệp', 'robot dịch vụ', 'robot phẫu thuật', 'robot tự hành', 'drone giao hàng', 'drone nông nghiệp', 'thực tế ảo', 'thực tế tăng cường', 'thực tế hỗn hợp', 'mô phỏng 3D', 'đồ họa máy tính', 'công nghệ game', 'công nghệ đồ họa', 'công nghệ Unreal Engine', 'công nghệ Unity', 'blockchain', 'web3', 'hợp đồng thông minh', 'tài chính phi tập trung', 'ví kỹ thuật số', 'mã thông báo không thể thay thế (NFT)', 'game NFT', 'metaverse', 'vũ trụ số', 'avatar số', 'không gian ảo', 'công nghệ 5G', 'công nghệ 6G', 'mạng vệ tinh', 'internet vạn vật', 'thành phố thông minh', 'tòa nhà thông minh', 'giao thông thông minh', 'công nghệ Wi-Fi 6', 'công nghệ Li-Fi', 'công nghệ blockchain Ethereum', 'công nghệ blockchain Solana', 'công nghệ blockchain Polkadot', 'an ninh mạng', 'bảo mật đám mây', 'bảo mật IoT', 'bảo mật blockchain', 'bảo mật lượng tử', 'an ninh zero trust', 'tường lửa thế hệ mới', 'mã hóa dữ liệu', 'xác thực đa yếu tố', 'quản lý danh tính số', 'công nghệ sinh trắc học', 'nhận diện khuôn mặt', 'nhận diện giọng nói', 'phân tích hành vi người dùng', 'công nghệ giám sát', 'công nghệ chống DDoS', 'công nghệ VPN', 'công nghệ SD-WAN', 'công nghệ mạng riêng ảo', 'công nghệ lưu trữ đám mây', 'công nghệ sao lưu dữ liệu', 'công nghệ phục hồi thảm họa', 'công nghệ lưu trữ phi tập trung', 'công nghệ IPFS', 'công nghệ phân tích thời gian thực', 'công nghệ xử lý dữ liệu lớn', 'công nghệ Apache Kafka', 'công nghệ Apache Spark', 'công nghệ Hadoop', 'công nghệ Elasticsearch', 'công nghệ Tableau', 'công nghệ Power BI', 'công nghệ phân tích kinh doanh', 'công nghệ phân tích khách hàng', 'công nghệ phân tích thị trường', 'công nghệ phân tích tài chính', 'công nghệ phân tích rủi ro', 'công nghệ phân tích chuỗi cung ứng', 'công nghệ tối ưu hóa chuỗi cung ứng', 'công nghệ quản lý kho', 'công nghệ logistics thông minh', 'công nghệ quản lý vận tải', 'công nghệ giao hàng tự động', 'công nghệ xe tự hành', 'công nghệ xe điện', 'công nghệ pin lithium-ion', 'công nghệ pin trạng thái rắn', 'công nghệ sạc nhanh', 'công nghệ sạc không dây', 'công nghệ lưới điện thông minh', 'công năng lượng tái tạo', 'công nghệ năng lượng mặt trời', 'công nghệ năng lượng gió', 'công nghệ năng lượng thủy triều', 'công nghệ năng lượng địa nhiệt', 'công nghệ năng lượng sinh khối', 'công nghệ năng lượng hydro xanh', 'công nghệ lưu trữ năng lượng', 'công nghệ pin lưu trữ', 'công nghệ siêu tụ điện', 'công nghệ vật liệu nano', 'công nghệ graphene', 'công nghệ in 3D', 'công nghệ in 4D', 'công nghệ vật liệu thông minh', 'công nghệ vật liệu sinh học', 'công nghệ polymer tiên tiến', 'công nghệ gốm tiên tiến', 'công nghệ composite tiên tiến', 'công nghệ siêu dẫn', 'công nghệ siêu vật liệu', 'công nghệ quang tử', 'công nghệ laser', 'công nghệ cảm biến quang học', 'công nghệ radar', 'công nghệ lidar', 'công nghệ định vị GPS', 'công nghệ định vị RTK', 'công nghệ định vị trong nhà', 'công nghệ bản đồ số', 'công nghệ GIS', 'công nghệ thực tế địa lý', 'công nghệ khảo sát từ xa', 'công nghệ vệ tinh', 'công nghệ vệ tinh nhỏ', 'công nghệ cubesat', 'công nghệ truyền thông vệ tinh', 'công nghệ quan sát Trái Đất', 'công nghệ thời tiết số', 'công nghệ dự báo thời tiết', 'công nghệ mô phỏng khí hậu', 'công nghệ phân tích môi trường', 'công nghệ giám sát môi trường', 'công nghệ IoT môi trường', 'công nghệ cảm biến môi trường', 'công nghệ phân tích chất lượng không khí', 'công nghệ phân tích chất lượng nước', 'công nghệ quản lý tài nguyên nước', 'công nghệ tưới tiêu thông minh', 'công nghệ nông nghiệp chính xác', 'công nghệ nông nghiệp thông minh', 'công nghệ nông nghiệp thẳng đứng', 'công nghệ thủy canh', 'công nghệ khí canh', 'công nghệ đất thông minh', 'công nghệ cảm biến đất', 'công nghệ phân tích đất', 'công nghệ phân bón thông minh', 'công nghệ thuốc trừ sâu sinh học', 'công nghệ kiểm soát côn trùng', 'công nghệ nông nghiệp hữu cơ', 'công nghệ nông nghiệp tái sinh', 'công nghệ chăn nuôi thông minh', 'công nghệ nuôi trồng thủy sản', 'công nghệ nuôi trồng tảo', 'công nghệ thực phẩm bền vững', 'công nghệ thực phẩm nhân tạo', 'công nghệ thịt nuôi cấy', 'công nghệ protein thay thế', 'công nghệ thực phẩm in 3D', 'công nghệ đóng gói thông minh', 'công nghệ bảo quản thực phẩm', 'công nghệ chuỗi cung ứng lạnh', 'công nghệ truy xuất nguồn gốc thực phẩm', 'công nghệ blockchain thực phẩm', 'công nghệ IoT thực phẩm', 'công nghệ phân tích thực phẩm', 'công nghệ kiểm tra an toàn thực phẩm', 'công nghệ tiêu chuẩn thực phẩm', 'công nghệ HACCP', 'công nghệ ISO 22000', 'công nghệ sản xuất thực phẩm', 'công nghệ chế biến thực phẩm', 'công nghệ tự động hóa thực phẩm', 'công nghệ robot nhà bếp', 'công nghệ nhà hàng thông minh', 'công nghệ đặt món trực tuyến', 'công nghệ giao đồ ăn', 'công nghệ ứng dụng giao đồ ăn', 'công nghệ thanh toán không tiếp xúc', 'công nghệ thanh toán di động', 'công nghệ ví điện tử', 'công nghệ ngân hàng số', 'công nghệ fintech', 'công nghệ ngân hàng mở', 'công nghệ API ngân hàng', 'công nghệ tài chính cá nhân', 'công nghệ quản lý tài sản', 'công nghệ đầu tư tự động', 'công nghệ robo-advisor', 'công nghệ giao dịch chứng khoán', 'công nghệ giao dịch tiền điện tử', 'công nghệ sàn giao dịch phi tập trung', 'công nghệ ví tiền điện tử', 'công nghệ staking tiền điện tử', 'công nghệ yield farming', 'công nghệ lending tiền điện tử', 'công nghệ stablecoin', 'công nghệ CBDC', 'công nghệ tiền kỹ thuật số', 'công nghệ blockchain tài chính', 'công nghệ bảo hiểm số', 'công nghệ insurtech', 'công nghệ phân tích rủi ro bảo hiểm', 'công nghệ bảo hiểm vi mô', 'công nghệ bảo hiểm theo yêu cầu', 'công nghệ hợp đồng bảo hiểm thông minh', 'công nghệ phân tích dữ liệu bảo hiểm', 'công nghệ chăm sóc khách hàng', 'công nghệ CRM', 'công nghệ ERP', 'công nghệ quản lý doanh nghiệp', 'công nghệ quản lý nhân sự', 'công nghệ tuyển dụng trực tuyến', 'công nghệ học trực tuyến', 'công nghệ giáo dục số', 'công nghệ lớp học ảo', 'công nghệ thực tế ảo giáo dục', 'công nghệ gamification giáo dục', 'công nghệ học cá nhân hóa', 'công nghệ AI giáo dục', 'công nghệ phân tích học tập', 'công nghệ học tập thích nghi', 'công nghệ MOOC', 'công nghệ khóa học trực tuyến', 'công nghệ nền tảng học trực tuyến', 'công nghệ công cụ học trực tuyến', 'công nghệ Zoom', 'công nghệ Microsoft Teams', 'công nghệ Google Classroom', 'công nghệ công cụ họp trực tuyến', 'công nghệ hội nghị truyền hình', 'công nghệ làm việc từ xa', 'công nghệ văn phòng số', 'công nghệ công cụ cộng tác', 'công nghệ quản lý dự án', 'công nghệ Trello', 'công nghệ Asana', 'công nghệ Jira', 'công nghệ Slack', 'công nghệ công cụ giao tiếp', 'công nghệ bảo mật giao tiếp', 'công nghệ mã hóa giao tiếp', 'công nghệ lưu trữ tài liệu', 'công nghệ Google Drive', 'công nghệ Dropbox', 'công nghệ OneDrive', 'công nghệ quản lý tài liệu', 'công nghệ chữ ký điện tử', 'công nghệ hợp đồng điện tử', 'công nghệ tự động hóa văn phòng', 'công nghệ RPA', 'công nghệ tự động hóa quy trình', 'công nghệ quy trình kinh doanh', 'công nghệ quản lý quy trình', 'công nghệ BPM', 'công nghệ phân tích quy trình', 'công nghệ tối ưu hóa quy trình', 'công nghệ chuyển đổi số', 'công nghệ công nghiệp 4.0', 'công nghệ sản xuất thông minh', 'công nghệ nhà máy thông minh', 'công nghệ tự động hóa nhà máy', 'công nghệ robot sản xuất', 'công nghệ IoT sản xuất', 'công nghệ cảm biến sản xuất', 'công nghệ phân tích sản xuất', 'công nghệ bảo trì dự đoán', 'công nghệ quản lý tài sản', 'công nghệ EAM', 'công nghệ CMMS', 'công nghệ quản lý vòng đời sản phẩm', 'công nghệ PLM', 'công nghệ thiết kế sản phẩm', 'công nghệ CAD', 'công nghệ CAM', 'công nghệ CAE', 'công nghệ mô phỏng sản phẩm', 'công nghệ thực tế ảo sản phẩm', 'công nghệ bản sao số', 'công nghệ digital twin', 'công nghệ mô phỏng số', 'công nghệ phân tích số', 'công nghệ tối ưu hóa số', 'công nghệ phân tích hiệu suất', 'công nghệ phân tích tài sản', 'công nghệ phân tích năng lượng', 'công nghệ tối ưu hóa năng lượng', 'công nghệ quản lý năng lượng', 'công nghệ EMS', 'công nghệ tòa nhà thông minh', 'công nghệ BMS', 'công nghệ quản lý tòa nhà', 'công nghệ cảm biến tòa nhà', 'công nghệ phân tích tòa nhà', 'công nghệ bảo mật tòa nhà', 'công nghệ an ninh tòa nhà', 'công nghệ camera thông minh', 'công nghệ nhận diện biển số', 'công nghệ kiểm soát ra vào', 'công nghệ thẻ thông minh', 'công nghệ IoT tòa nhà', 'công nghệ phân tích không gian', 'công nghệ tối ưu hóa không gian', 'công nghệ quản lý không gian', 'công nghệ thiết kế nội thất', 'công nghệ nội thất thông minh', 'công nghệ nội thất bền vững', 'công nghệ vật liệu nội thất', 'công nghệ thời trang thông minh', 'công nghệ thời trang bền vững', 'công nghệ tái chế thời trang', 'công nghệ vải thông minh', 'công nghệ vải bền vững', 'công nghệ may mặc thông minh', 'công nghệ thiết kế thời trang', 'công nghệ phần mềm thiết kế', 'công nghệ Adobe Illustrator', 'công nghệ Adobe Photoshop', 'công nghệ Canva', 'công nghệ thiết kế đồ họa', 'công nghệ thiết kế UI/UX', 'công nghệ trải nghiệm người dùng', 'công nghệ thiết kế giao diện', 'công nghệ thiết kế sản phẩm', 'công nghệ thiết kế công nghiệp', 'công nghệ thiết kế bền vững', 'công nghệ thiết kế sinh thái', 'công nghệ kiến trúc thông minh', 'công nghệ kiến trúc bền vững', 'công nghệ BIM', 'công nghệ mô phỏng kiến trúc', 'công nghệ thiết kế đô thị', 'công nghệ quy hoạch đô thị', 'công nghệ đô thị thông minh', 'công nghệ giao thông đô thị', 'công nghệ xe đạp chia sẻ', 'công nghệ xe điện chia sẻ', 'công nghệ phương tiện công cộng', 'công nghệ giao thông công cộng', 'công nghệ quản lý giao thông', 'công nghệ ITS', 'công nghệ phân tích giao thông', 'công nghệ tối ưu hóa giao thông', 'công nghệ bản đồ giao thông', 'công nghệ định tuyến thông minh', 'công nghệ định tuyến thời gian thực', 'công nghệ xe tự hành đô thị', 'công nghệ xe điện đô thị', 'công nghệ pin xe điện', 'công nghệ sạc xe điện', 'công nghệ trạm sạc xe điện', 'công nghệ lưới sạc xe điện', 'công nghệ năng lượng xe điện', 'công nghệ xe hydro', 'công nghệ xe tự hành cấp 4', 'công nghệ xe tự hành cấp 5', 'công nghệ cảm biến xe tự hành', 'công nghệ lidar xe tự hành', 'công nghệ radar xe tự hành', 'công nghệ camera xe tự hành', 'công nghệ AI xe tự hành', 'công nghệ phân tích giao thông', 'công nghệ an toàn giao thông', 'công nghệ giám sát giao thông', 'công nghệ phân tích tai nạn', 'công nghệ quản lý tai nạn', 'công nghệ cứu hộ giao thông', 'công nghệ y tế giao thông', 'công nghệ sơ cứu', 'công nghệ y tế khẩn cấp', 'công nghệ xe cứu thương thông minh', 'công nghệ IoT y tế', 'công nghệ cảm biến y tế', 'công nghệ thiết bị y tế', 'công nghệ thiết bị đeo y tế', 'công nghệ đồng hồ thông minh', 'công nghệ vòng đeo sức khỏe', 'công nghệ theo dõi sức khỏe', 'công nghệ phân tích sức khỏe', 'công nghệ y học cá nhân hóa', 'công nghệ y học chính xác', 'công nghệ di truyền học', 'công nghệ chỉnh sửa gen', 'công nghệ CRISPR', 'công nghệ sinh học tổng hợp', 'công nghệ sinh học y tế', 'công nghệ sinh học nông nghiệp', 'công nghệ sinh học môi trường', 'công nghệ vi sinh vật học', 'công nghệ công nghệ sinh học biển', 'công nghệ nuôi cấy mô', 'công nghệ tế bào gốc', 'công nghệ liệu pháp gen', 'công nghệ vắc-xin mRNA', 'công nghệ vắc-xin công nghệ cao', 'công nghệ sản xuất vắc-xin', 'công nghệ phân phối vắc-xin', 'công nghệ chuỗi cung ứng vắc-xin', 'công nghệ y tế từ xa', 'công nghệ telemedicine', 'công nghệ tư vấn y tế trực tuyến', 'công nghệ hồ sơ y tế điện tử', 'công nghệ EMR', 'công nghệ EHR', 'công nghệ quản lý bệnh viện', 'công nghệ phân tích bệnh viện', 'công nghệ tối ưu hóa bệnh viện', 'công nghệ robot phẫu thuật', 'công nghệ phẫu thuật từ xa', 'công nghệ phẫu thuật nội soi', 'công nghệ phẫu thuật laser', 'công nghệ chẩn đoán hình ảnh', 'công nghệ AI chẩn đoán', 'công nghệ phân tích hình ảnh y tế', 'công nghệ X-quang số', 'công nghệ MRI', 'công nghệ CT scan', 'công nghệ siêu âm', 'công nghệ cảm biến y tế', 'công nghệ thiết bị y tế thông minh', 'công nghệ IoT bệnh viện', 'công nghệ phân tích dữ liệu y tế', 'công nghệ big data y tế', 'công nghệ phân tích bệnh nhân', 'công nghệ dự đoán bệnh', 'công nghệ quản lý bệnh mãn tính', 'công nghệ chăm sóc sức khỏe tại nhà', 'công nghệ chăm sóc người cao tuổi', 'công nghệ thiết bị hỗ trợ người cao tuổi', 'công nghệ robot chăm sóc', 'công nghệ nhà thông minh y tế', 'công nghệ cảm biến nhà thông minh', 'công nghệ phân tích nhà thông minh', 'công nghệ an ninh nhà thông minh', 'công nghệ chiếu sáng thông minh', 'công nghệ điều hòa thông minh', 'công nghệ thiết bị gia dụng thông minh', 'công nghệ IoT gia đình', 'công nghệ cảm biến gia đình', 'công nghệ quản lý năng lượng gia đình', 'công nghệ tối ưu hóa năng lượng gia đình', 'công nghệ năng lượng mặt trời gia đình', 'công nghệ pin lưu trữ gia đình', 'công nghệ lưới điện gia đình', 'công nghệ nhà thông minh bền vững', 'công nghệ tái chế tại nhà', 'công nghệ quản lý rác thải', 'công nghệ tái chế rác thải', 'công nghệ phân loại rác thải', 'công nghệ IoT rác thải', 'công nghệ cảm biến rác thải', 'công nghệ quản lý môi trường đô thị', 'công nghệ giám sát môi trường đô thị', 'công nghệ phân tích môi trường đô thị', 'công nghệ chất lượng không khí đô thị', 'công nghệ chất lượng nước đô thị', 'công nghệ quản lý tài nguyên đô thị', 'công nghệ tái chế đô thị', 'công nghệ kinh tế tuần hoàn đô thị', 'công nghệ phát triển bền vững đô thị', 'công nghệ carbon neutral đô thị', 'công nghệ giảm phát thải đô thị', 'công nghệ năng lượng tái tạo đô thị', 'công nghệ năng lượng mặt trời đô thị', 'công nghệ năng lượng gió đô thị', 'công nghệ năng lượng hydro đô thị', 'công nghệ lưu trữ năng lượng đô thị', 'công nghệ lưới điện thông minh đô thị', 'công nghệ quản lý năng lượng đô thị', 'công nghệ tối ưu hóa năng lượng đô thị', 'công nghệ giao thông xanh đô thị', 'công nghệ xe điện đô thị', 'công nghệ xe hydro đô thị', 'công nghệ phương tiện xanh đô thị', 'công nghệ cơ sở hạ tầng xanh đô thị', 'công nghệ tòa nhà xanh đô thị', 'công nghệ công viên đô thị', 'công nghệ không gian xanh đô thị', 'công nghệ nông nghiệp đô thị', 'công nghệ nông nghiệp thẳng đứng đô thị', 'công nghệ thủy canh đô thị', 'công nghệ khí canh đô thị', 'công nghệ thực phẩm đô thị', 'công nghệ thực phẩm bền vững đô thị', 'công nghệ chuỗi cung ứng thực phẩm đô thị', 'công nghệ truy xuất nguồn gốc thực phẩm đô thị', 'công nghệ blockchain thực phẩm đô thị', 'công nghệ IoT thực phẩm đô thị', 'công nghệ phân tích thực phẩm đô thị', 'công nghệ an toàn thực phẩm đô thị', 'công nghệ tiêu chuẩn thực phẩm đô thị', 'công nghệ sản xuất thực phẩm đô thị', 'công nghệ chế biến thực phẩm đô thị', 'công nghệ tự động hóa thực phẩm đô thị', 'công nghệ nhà hàng thông minh đô thị', 'công nghệ giao đồ ăn đô thị', 'công nghệ ứng dụng giao đồ ăn đô thị', 'công nghệ thanh toán không tiếp xúc đô thị', 'công nghệ thanh toán di động đô thị', 'công nghệ ví điện tử đô thị', 'công nghệ ngân hàng số đô thị', 'công nghệ fintech đô thị', 'công nghệ ngân hàng mở đô thị', 'công nghệ tài chính cá nhân đô thị', 'công nghệ quản lý tài sản đô thị', 'công nghệ đầu tư tự động đô thị', 'công nghệ robo-advisor đô thị', 'công nghệ giao dịch chứng khoán đô thị', 'công nghệ giao dịch tiền điện tử đô thị', 'công technology sàn giao dịch phi tập trung đô thị', 'công nghệ ví tiền điện tử đô thị', 'công nghệ staking tiền điện tử đô thị', 'công technology yield farming đô thị', 'công technology lending tiền điện tử đô thị', 'công technology stablecoin đô thị', 'công technology CBDC đô thị', 'công technology tiền kỹ thuật số đô thị', 'công technology blockchain tài chính đô thị', 'công technology bảo hiểm số đô thị', 'công technology insurtech đô thị', 'công technology phân tích rủi ro bảo hiểm đô thị', 'công technology bảo hiểm vi mô đô thị', 'công technology bảo hiểm theo yêu cầu đô thị', 'công technology hợp đồng bảo hiểm thông minh đô thị', 'công technology phân tích dữ liệu bảo hiểm đô thị', 'công technology chăm sóc khách hàng đô thị', 'công technology CRM đô thị', 'công technology ERP đô thị', 'công technology quản lý doanh nghiệp đô thị', 'công technology quản lý nhân sự đô thị', 'công technology tuyển dụng trực tuyến đô thị', 'công technology học trực tuyến đô thị', 'công technology giáo dục số đô thị', 'công technology lớp học ảo đô thị', 'công technology thực tế ảo giáo dục đô thị', 'công technology gamification giáo dục đô thị', 'công technology học cá nhân hóa đô thị', 'công technology AI giáo dục đô thị', 'công technology phân tích học tập đô thị', 'công technology học tập thích nghi đô thị', 'công technology MOOC đô thị', 'công technology khóa học trực tuyến đô thị', 'công technology nền tảng học trực tuyến đô thị', 'công technology công cụ học trực tuyến đô thị', 'công technology Zoom đô thị', 'công technology Microsoft Teams đô thị', 'công technology Google Classroom đô thị', 'công technology công cụ họp trực tuyến đô thị', 'công technology hội nghị truyền hình đô thị', 'công technology làm việc từ xa đô thị', 'công technology văn phòng số đô thị', 'công technology công cụ cộng tác đô thị', 'công technology quản lý dự án đô thị', 'công technology Trello đô thị', 'công technology Asana đô thị', 'công technology Jira đô thị', 'công technology Slack đô thị', 'công technology công cụ giao tiếp đô thị', 'công technology bảo mật giao tiếp đô thị', 'công technology mã hóa giao tiếp đô thị', 'công technology lưu trữ tài liệu đô thị', 'công technology Google Drive đô thị', 'công technology Dropbox đô thị', 'công technology OneDrive đô thị', 'công technology quản lý tài liệu đô thị', 'công technology chữ ký điện tử đô thị', 'công technology hợp đồng điện tử đô thị', 'công technology tự động hóa văn phòng đô thị', 'công technology RPA đô thị', 'công technology tự động hóa quy trình đô thị', 'công technology quy trình kinh doanh đô thị', 'công technology quản lý quy trình đô thị', 'công technology BPM đô thị', 'công technology phân tích quy trình đô thị', 'công technology tối ưu hóa quy trình đô thị', 'công technology chuyển đổi số đô thị', 'công technology công nghiệp 4.0 đô thị', 'công technology sản xuất thông minh đô thị', 'công technology nhà máy thông minh đô thị', 'công technology tự động hóa nhà máy đô thị', 'công technology robot sản xuất đô thị', 'công technology IoT sản xuất đô thị', 'công technology cảm biến sản xuất đô thị', 'công technology phân tích sản xuất đô thị', 'công technology bảo trì dự đoán đô thị', 'công technology quản lý tài sản đô thị', 'công technology EAM đô thị', 'công technology CMMS đô thị', 'công technology quản lý vòng đời sản phẩm đô thị', 'công technology PLM đô thị', 'công technology thiết kế sản phẩm đô thị', 'công technology CAD đô thị', 'công technology CAM đô thị', 'công technology CAE đô thị', 'công technology mô phỏng sản phẩm đô thị', 'công technology thực tế ảo sản phẩm đô thị', 'công technology bản sao số đô thị', 'công technology digital twin đô thị', 'công technology mô phỏng số đô thị', 'công technology phân tích số đô thị', 'công technology tối ưu hóa số đô thị', 'công technology phân tích hiệu suất đô thị', 'công technology phân tích tài sản đô thị', 'công technology phân tích năng lượng đô thị', 'công technology tối ưu hóa năng lượng đô thị', 'công technology quản lý năng lượng đô thị', 'công technology EMS đô thị', 'công technology tòa nhà thông minh đô thị', 'công technology BMS đô thị', 'công technology quản lý tòa nhà đô thị', 'công technology cảm biến tòa nhà đô thị', 'công technology phân tích tòa nhà đô thị', 'công technology bảo mật tòa nhà đô thị', 'công technology an ninh tòa nhà đô thị', 'công technology camera thông minh đô thị', 'công technology nhận diện biển số đô thị', 'công technology kiểm soát ra vào đô thị', 'công technology thẻ thông minh đô thị', 'công technology IoT tòa nhà đô thị', 'công technology phân tích không gian đô thị', 'công technology tối ưu hóa không gian đô thị', 'công technology quản lý không gian đô thị', 'công technology thiết kế nội thất đô thị', 'công technology nội thất thông minh đô thị', 'công technology nội thất bền vững đô thị', 'công technology vật liệu nội thất đô thị', 'công technology thời trang thông minh đô thị', 'công technology thời trang bền vững đô thị', 'công technology tái chế thời trang đô thị', 'công technology vải thông minh đô thị', 'công technology vải bền vững đô thị', 'công technology may mặc thông minh đô thị', 'công technology thiết kế thời trang đô thị', 'công technology phần mềm thiết kế đô thị', 'công technology Adobe Illustrator đô thị', 'công technology Adobe Photoshop đô thị', 'công technology Canva đô thị', 'công technology thiết kế đồ họa đô thị', 'công technology thiết kế UI/UX đô thị', 'công technology trải nghiệm người dùng đô thị', 'công technology thiết kế giao diện đô thị', 'công technology thiết kế sản phẩm đô thị', 'công technology thiết kế công nghiệp đô thị', 'công technology thiết kế bền vững đô thị', 'công technology thiết kế sinh thái đô thị', 'công technology kiến trúc thông minh đô thị', 'công technology kiến trúc bền vững đô thị', 'công technology BIM đô thị', 'công technology mô phỏng kiến trúc đô thị', 'công technology thiết kế đô thị', 'công technology quy hoạch đô thị', 'công technology đô thị thông minh', 'công technology giao thông đô thị', 'công technology xe đạp chia sẻ đô thị', 'công technology xe điện chia sẻ đô thị', 'công technology phương tiện công cộng đô thị', 'công technology giao thông công cộng đô thị', 'công technology quản lý giao thông đô thị', 'công technology ITS đô thị', 'công technology phân tích giao thông đô thị', 'công technology tối ưu hóa giao thông đô thị', 'công technology bản đồ giao thông đô thị', 'công technology định tuyến thông minh đô thị', 'công technology định tuyến thời gian thực đô thị', 'công technology xe tự hành đô thị', 'công technology xe điện đô thị', 'công technology pin xe điện đô thị', 'công technology sạc xe điện đô thị', 'công technology trạm sạc xe điện đô thị', 'công technology lưới sạc xe điện đô thị', 'công technology năng lượng xe điện đô thị', 'công technology xe hydro đô thị', 'công technology xe tự hành cấp 4 đô thị', 'công technology xe tự hành cấp 5 đô thị', 'công technology cảm biến xe tự hành đô thị', 'công technology lidar xe tự hành đô thị', 'công technology radar xe tự hành đô thị', 'công technology camera xe tự hành đô thị', 'công technology AI xe tự hành đô thị', 'công technology phân tích giao thông đô thị', 'công technology an toàn giao thông đô thị', 'công technology giám sát giao thông đô thị', 'công technology phân tích tai nạn đô thị', 'công technology quản lý tai nạn đô thị', 'công technology cứu hộ giao thông đô thị', 'công technology y tế giao thông đô thị', 'công technology sơ cứu đô thị', 'công technology y tế khẩn cấp đô thị', 'công technology xe cứu thương thông minh đô thị', 'công technology IoT y tế đô thị', 'công technology cảm biến y tế đô thị', 'công technology thiết bị y tế đô thị', 'công technology thiết bị đeo y tế đô thị', 'công technology đồng hồ thông minh đô thị', 'công technology vòng đeo sức khỏe đô thị', 'công technology theo dõi sức khỏe đô thị', 'công technology phân tích sức khỏe đô thị', 'công technology y học cá nhân hóa đô thị', 'công technology y học chính xác đô thị', 'công technology di truyền học đô thị', 'công technology chỉnh sửa gen đô thị', 'công technology CRISPR đô thị', 'công technology sinh học tổng hợp đô thị', 'công technology sinh học y tế đô thị', 'công technology sinh học nông nghiệp đô thị', 'công technology sinh học môi trường đô thị', 'công technology vi sinh vật học đô thị', 'công technology công nghệ sinh học biển đô thị', 'công technology nuôi cấy mô đô thị', 'công technology tế bào gốc đô thị', 'công technology liệu pháp gen đô thị', 'công technology vắc-xin mRNA đô thị', 'công technology vắc-xin công nghệ cao đô thị', 'công technology sản xuất vắc-xin đô thị', 'công technology phân phối vắc-xin đô thị', 'công technology chuỗi cung ứng vắc-xin đô thị', 'công technology y tế từ xa đô thị', 'công technology telemedicine đô thị', 'công technology tư vấn y tế trực tuyến đô thị', 'công technology hồ sơ y tế điện tử đô thị', 'công technology EMR đô thị', 'công technology EHR đô thị', 'công technology quản lý bệnh viện đô thị', 'công technology phân tích bệnh viện đô thị', 'công technology tối ưu hóa bệnh viện đô thị', 'công technology robot phẫu thuật đô thị', 'công technology phẫu thuật từ xa đô thị', 'công technology phẫu thuật nội soi đô thị', 'công technology phẫu thuật laser đô thị', 'công technology chẩn đoán hình ảnh đô thị', 'công technology AI chẩn đoán đô thị', 'công technology phân tích hình ảnh y tế đô thị', 'công technology X-quang số đô thị', 'công technology MRI đô thị', 'công technology CT scan đô thị', 'công technology siêu âm đô thị', 'công technology cảm biến y tế đô thị', 'công technology thiết bị y tế thông minh đô thị', 'công technology IoT bệnh viện đô thị', 'công technology phân tích dữ liệu y tế đô thị', 'công technology big data y tế đô thị', 'công technology phân tích bệnh nhân đô thị', 'công technology dự đoán bệnh đô thị', 'công technology quản lý bệnh mãn tính đô thị', 'công technology chăm sóc sức khỏe tại nhà đô thị', 'công technology chăm sóc người cao tuổi đô thị', 'công technology thiết bị hỗ trợ người cao tuổi đô thị', 'công technology robot chăm sóc đô thị', 'công technology nhà thông minh y tế đô thị', 'công technology cảm biến nhà thông minh đô thị', 'công technology phân tích nhà thông minh đô thị', 'công technology an ninh nhà thông minh đô thị', 'công technology chiếu sáng thông minh đô thị', 'công technology điều hòa thông minh đô thị', 'công technology thiết bị gia dụng thông minh đô thị', 'công technology IoT gia đình đô thị', 'công technology cảm biến gia đình đô thị', 'công technology quản lý năng lượng gia đình đô thị', 'công technology tối ưu hóa năng lượng gia đình đô thị', 'công technology năng lượng mặt trời gia đình đô thị', 'công technology pin lưu trữ gia đình đô thị', 'công technology lưới điện gia đình đô thị', 'công technology nhà thông minh bền vững đô thị', 'công technology tái chế tại nhà đô thị', 'công technology quản lý rác thải đô thị', 'công technology tái chế rác thải đô thị', 'công technology phân loại rác thải đô thị', 'công technology IoT rác thải đô thị']


driver = None

def signal_handler(sig, frame):
    logging.info("🛑 Đã nhận tín hiệu hủy (Ctrl+C). Đang đóng trình duyệt...")
    if driver:
        try:
            driver.quit()
        except:
            pass
    logging.info("✅ Chương trình đã thoát.")
    sys.exit(0)

def load_keyword_cache():
    try:
        if os.path.exists(KEYWORD_CACHE_FILE):
            with open(KEYWORD_CACHE_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f).get('used_keywords', []))
        return set()
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi tải cache từ khóa: {e}")
        return set()

def save_keyword_cache(used_keywords):
    try:
        with open(KEYWORD_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'used_keywords': list(used_keywords)}, f, ensure_ascii=False)
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi lưu cache từ khóa: {e}")

def get_hot_keywords(period="daily"):
    cache_file = HOT_KEYWORDS_FILE
    today = datetime.now().date()
    cache_expiry = today - timedelta(days=KEYWORD_CACHE_DAYS)

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        cache_date = datetime.strptime(cache.get("date"), "%Y-%m-%d").date()
        if cache_date >= cache_expiry and len(cache.get("keywords", [])) >= 30 and cache.get("period") == period:
            logging.info(f"📚 Sử dụng từ khóa hot từ cache ({period}).")
            return cache["keywords"]

    try:
        logging.info(f"🌐 Lấy từ khóa hot từ Google Trends (khu vực: Vietnam, kỳ: {period})...")
        pytrends = TrendReq(hl="vi-VN", tz=420, timeout=(3, 7))
        
        if period == "daily":
            trending_searches = pytrends.trending_searches(pn="vietnam").head(50)[0].tolist()
        elif period == "weekly":
            pytrends.build_payload(kw_list=["bảo mật"], timeframe='now 7-d', geo='VN')
            trending_searches = pytrends.related_queries()['top']['query'].tolist()
            #trending_searches = pytrends.related_queries()['bảo mật']['top']['query'].tolist()
        elif period == "monthly":
            pytrends.build_payload(kw_list=["bảo mật"], timeframe='now 30-d', geo='VN')
            trending_searches = pytrends.related_queries()['top']['query'].tolist()
            #trending_searches = pytrends.related_queries()['bảo mật']['top']['query'].tolist()
        elif period == "yearly":
            pytrends.build_payload(kw_list=["bảo mật"], timeframe='today 12-m', geo='VN')
            trending_searches = pytrends.related_queries()['top']['query'].tolist()
            #trending_searches = pytrends.related_queries()['bảo mật']['top']['query'].tolist()
        else:
            trending_searches = pytrends.trending_searches(pn="vietnam").head(50)[0].tolist()

        if not trending_searches or len(trending_searches) < 30:
            logging.warning("⚠️ Không đủ từ khóa từ Google Trends, sử dụng FALLBACK_KEYWORDS.")
            return FALLBACK_KEYWORDS

        cache = {"date": today.strftime("%Y-%m-%d"), "period": period, "keywords": trending_searches}
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        logging.info(f"✅ Đã lưu {len(trending_searches)} từ khóa hot.")
        return trending_searches
    except Exception as e:
        logging.error(f"⚠️ Lỗi lấy Google Trends: {str(e)}")
        logging.info("ℹ️ Sử dụng từ khóa dự phòng.")
        return FALLBACK_KEYWORDS

def init_driver(headless=True):
    logging.info("Đang khởi tạo Edge driver...")
    try:
        service = Service(EDGE_DRIVER_PATH)
        options = Options()
        mobile_emulation = {"deviceName": "iPhone X"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 EdgiOS/46.3.23 Mobile/15E148 Safari/605.1.15")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--disable-gpu")
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Edge(service=service, options=options)
        driver.set_page_load_timeout(30)
        logging.info("✅ Edge driver khởi tạo thành công!")
        return driver
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi khởi tạo driver: {e}")
        return None

def tick_recaptcha_if_present(driver):
    try:
        iframe = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]"))
        )
        driver.switch_to.frame(iframe)
        logging.info("🔍 Tìm thấy reCAPTCHA, đang tick...")
        checkbox = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
        )
        checkbox.click()
        logging.info("✅ Đã tick reCAPTCHA")
        driver.switch_to.default_content()
        time.sleep(1)
    except TimeoutException:
        logging.info("ℹ️ Không có reCAPTCHA trên trang này.")
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi xử lý reCAPTCHA: {e}")

def get_page_hash(driver):
    try:
        return hashlib.sha256(driver.page_source.encode()).hexdigest()
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi tính hash: {e}")
        return ""

def login_if_needed(driver):
    try:
        driver.get("https://www.bing.com/rewards/panelflyout?partnerId=MemberCenterMobile")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "promo_card"))
        )
        try:
            login_button = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Sign in')]"))
            )
            login_button.click()
            logging.info("Đang đăng nhập...")
            email_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "i0116"))
            )
            email_field.send_keys("YOUR_EMAIL")  # Thay bằng email của bạn
            email_field.send_keys(Keys.ENTER)
            password_field = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "i0118"))
            )
            password_field.send_keys("YOUR_PASSWORD")  # Thay bằng mật khẩu của bạn
            password_field.send_keys(Keys.ENTER)
            WebDriverWait(driver, 15).until(
                EC.url_contains("rewards")
            )
            logging.info("✅ Đăng nhập thành công!")
        except TimeoutException:
            logging.info("ℹ️ Đã đăng nhập hoặc không cần đăng nhập.")
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi đăng nhập: {e}")

def check_search_completion(driver):
    try:
        driver.get("https://www.bing.com/rewards/panelflyout")
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "promo_cont"))
        )
        logging.info("⏳ Đang tạm dừng 5 giây để xem trang panelflyout...")
        time.sleep(5)
        try:
            points = driver.find_element(By.XPATH, "//div[@class='daily_search_row']/span[2]").text
            logging.info(f"✅ Points hiện tại: {points}")
            return True
        except NoSuchElementException:
            logging.warning("⚠️ Không tìm thấy phần tử điểm số, thử kiểm tra trang chính...")
            driver.get("https://www.bing.com")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            logging.info("✅ Trang Bing tải thành công, giả định tìm kiếm hoàn tất.")
            return True
    except Exception as e:
        logging.error(f"⚠️ Lỗi khi kiểm tra hoàn tất tìm kiếm: {e}")
        return False

def search_bing(driver, keyword):
    logging.info(f"🔍 Đang thực hiện tìm kiếm: {keyword}")
    for attempt in range(MAX_RETRIES):
        try:
            driver.get("https://www.bing.com")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "sb_form_q"))
            )
            tick_recaptcha_if_present(driver)
            search_box = driver.find_element(By.ID, "sb_form_q")
            search_box.clear()
            search_box.send_keys(keyword)
            search_box.send_keys(Keys.RETURN)
            logging.info(f"✅ Đã nhập và tìm kiếm: {keyword}")
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "b_results"))
            )
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(random.uniform(0.5, 2))
            results = driver.find_elements(By.CSS_SELECTOR, "#b_results .b_algo h2 a")
            if results:
                random.choice(results[:3]).click()
                time.sleep(random.uniform(1, 3))
            else:
                logging.warning("⚠️ Không tìm thấy kết quả, vẫn tiếp tục...")
            logging.info("✅ Kết quả tìm kiếm đã tải và tương tác.")
            return check_search_completion(driver)
        except TimeoutException:
            logging.error(f"❌ Timeout khi tải trang hoặc kết quả (lần {attempt + 1}/{MAX_RETRIES}).")
        except Exception as e:
            logging.error(f"⚠️ Lỗi trong quá trình tìm kiếm (lần {attempt + 1}/{MAX_RETRIES}): {e}")
        time.sleep(random.uniform(1, 3))
    logging.error(f"❌ Tìm kiếm {keyword} thất bại sau {MAX_RETRIES} lần.")
    return False

def main():
    global driver
    driver = init_driver(headless=True)
    if not driver:
        logging.error("❌ Không thể khởi tạo driver, thoát chương trình.")
        return

    signal.signal(signal.SIGINT, signal_handler)

    try:
        login_if_needed(driver)
        used_keywords = load_keyword_cache()
        last_keyword_fetch_date = None
        keywords = []

        while True:
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_keyword_fetch_date != current_date:
                keywords = get_hot_keywords(period=TREND_PERIOD)
                last_keyword_fetch_date = current_date
                logging.info(f"📋 Số từ khóa hot ({TREND_PERIOD}): {len(keywords)}")

            available_keywords = [k for k in keywords if k not in used_keywords]
            if not available_keywords:
                logging.warning("⚠️ Hết từ khóa hot, sử dụng mảng dự phòng...")
                available_keywords = [k for k in FALLBACK_KEYWORDS if k not in used_keywords]
                if not available_keywords:
                    logging.warning("⚠️ Hết từ khóa dự phòng, reset cache và sử dụng lại mảng dự phòng...")
                    used_keywords.clear()
                    save_keyword_cache(used_keywords)
                    available_keywords = FALLBACK_KEYWORDS

            # Randomly choose 1 to 3 searches
            num_searches = random.randint(1, 3)
            logging.info(f"🔍 Thực hiện {num_searches} tìm kiếm trong chu kỳ này.")

            for _ in range(num_searches):
                if not available_keywords:
                    logging.warning("⚠️ Hết từ khóa, reset cache...")
                    used_keywords.clear()
                    save_keyword_cache(used_keywords)
                    available_keywords = FALLBACK_KEYWORDS

                keyword = random.choice(available_keywords)
                used_keywords.add(keyword)
                save_keyword_cache(used_keywords)

                if search_bing(driver, keyword):
                    logging.info(f"✅ Tìm kiếm {keyword} hoàn tất.")
                else:
                    logging.warning(f"⚠️ Tìm kiếm {keyword} không thành công.")

                current_hash = get_page_hash(driver)
                logging.info(f"🔖 Hash trang hiện tại: {current_hash[:16]}...")
                time.sleep(random.uniform(3, 7))

            # Wait for approximately 5 minutes until next search cycle
            logging.info(f"⏳ Đợi {SEARCH_INTERVAL} giây đến chu kỳ tìm kiếm tiếp theo...")
            time.sleep(SEARCH_INTERVAL)

    except Exception as e:
        logging.error(f"❌ Lỗi trong vòng lặp chính: {e}")
        traceback.print_exc()
    finally:
        logging.info("🛑 Kết thúc chương trình.")
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()