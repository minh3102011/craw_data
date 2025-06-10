from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import time
import traceback
import hashlib
import os
from pytrends.request import TrendReq
from datetime import datetime
import json
import signal
import sys

# Đường dẫn đến msedgedriver.exe
EDGE_DRIVER_PATH = r"driver\msedgedriver.exe"

# URL Microsoft Rewards
REWARDS_URL = "https://rewards.bing.com/?form=edgepredeem"

# Danh sách từ khóa dự phòng lớn
FALLBACK_KEYWORDS = ['trí tuệ nhân tạo', ' học máy', ' học sâu', ' mạng nơ-ron', ' xử lý ngôn ngữ tự nhiên', ' thị giác máy tính', ' học liên kết', ' AI giải thích được', ' AI tổng quát', ' tự động hóa siêu tốc', ' chatbot', ' giọng nói nhân tạo', ' phân tích dự đoán', ' dữ liệu lớn', ' phân tích dữ liệu', ' điện toán đám mây', ' điện toán biên', ' điện toán lượng tử', ' phần mềm mã nguồn mở', ' DevOps', ' low code', ' no code', ' phát triển phần mềm', ' lập trình Python', ' lập trình Java', ' lập trình JavaScript', ' công nghệ API', ' microservices', ' containerization', ' Kubernetes', ' Docker', ' CI/CD', ' serverless computing', ' cơ sở dữ liệu phân tán', ' hệ thống nhúng', ' IoT công nghiệp', ' cảm biến thông minh', ' robot công nghiệp', ' robot dịch vụ', ' robot phẫu thuật', ' robot tự hành', ' drone giao hàng', ' drone nông nghiệp', ' thực tế ảo', ' thực tế tăng cường', ' thực tế hỗn hợp', ' mô phỏng 3D', ' đồ họa máy tính', ' công nghệ game', ' công nghệ đồ họa', ' công nghệ Unreal Engine', ' công nghệ Unity', ' blockchain', ' web3', ' hợp đồng thông minh', ' tài chính phi tập trung', ' ví kỹ thuật số', ' mã thông báo không thể thay thế (NFT)', ' game NFT', ' metaverse', ' vũ trụ số', ' avatar số', ' không gian ảo', ' công nghệ 5G', ' công nghệ 6G', ' mạng vệ tinh', ' internet vạn vật', ' thành phố thông minh', ' tòa nhà thông minh', ' giao thông thông minh', ' công nghệ Wi-Fi 6', ' công nghệ Li-Fi', ' công nghệ blockchain Ethereum', ' công nghệ blockchain Solana', ' công nghệ blockchain Polkadot', ' an ninh mạng', ' bảo mật đám mây', ' bảo mật IoT', ' bảo mật blockchain', ' bảo mật lượng tử', ' an ninh zero trust', ' tường lửa thế hệ mới', ' mã hóa dữ liệu', ' xác thực đa yếu tố', ' quản lý danh tính số', ' công nghệ sinh trắc học', ' nhận diện khuôn mặt', ' nhận diện giọng nói', ' phân tích hành vi người dùng', ' công nghệ giám sát', ' công nghệ chống DDoS', ' công nghệ VPN', ' công nghệ SD-WAN', ' công nghệ mạng riêng ảo', ' công nghệ lưu trữ đám mây', ' công nghệ sao lưu dữ liệu', ' công nghệ phục hồi thảm họa', ' công nghệ lưu trữ phi tập trung', ' công nghệ IPFS', ' công nghệ phân tích thời gian thực', ' công nghệ xử lý dữ liệu lớn', ' công nghệ Apache Kafka', ' công nghệ Apache Spark', ' công nghệ Hadoop', ' công nghệ Elasticsearch', ' công nghệ Tableau', ' công nghệ Power BI', ' công nghệ phân tích kinh doanh', ' công nghệ phân tích khách hàng', ' công nghệ phân tích thị trường', ' công nghệ phân tích tài chính', ' công nghệ phân tích rủi ro', ' công nghệ phân tích chuỗi cung ứng', ' công nghệ tối ưu hóa chuỗi cung ứng', ' công nghệ quản lý kho', ' công nghệ logistics thông minh', ' công nghệ quản lý vận tải', ' công nghệ giao hàng tự động', ' công nghệ xe tự hành', ' công nghệ xe điện', ' công nghệ pin lithium-ion', ' công nghệ pin trạng thái rắn', ' công nghệ sạc nhanh', ' công nghệ sạc không dây', ' công nghệ lưới điện thông minh', ' công năng lượng tái tạo', ' công nghệ năng lượng mặt trời', ' công nghệ năng lượng gió', ' công nghệ năng lượng thủy triều', ' công nghệ năng lượng địa nhiệt', ' công nghệ năng lượng sinh khối', ' công nghệ năng lượng hydro xanh', ' công nghệ lưu trữ năng lượng', ' công nghệ pin lưu trữ', ' công nghệ siêu tụ điện', ' công nghệ vật liệu nano', ' công nghệ graphene', ' công nghệ in 3D', ' công nghệ in 4D', ' công nghệ vật liệu thông minh', ' công nghệ vật liệu sinh học', ' công nghệ polymer tiên tiến', ' công nghệ gốm tiên tiến', ' công nghệ composite tiên tiến', ' công nghệ siêu dẫn', ' công nghệ siêu vật liệu', ' công nghệ quang tử', ' công nghệ laser', ' công nghệ cảm biến quang học', ' công nghệ radar', ' công nghệ lidar', ' công nghệ định vị GPS', ' công nghệ định vị RTK', ' công nghệ định vị trong nhà', ' công nghệ bản đồ số', ' công nghệ GIS', ' công nghệ thực tế địa lý', ' công nghệ khảo sát từ xa', ' công nghệ vệ tinh', ' công nghệ vệ tinh nhỏ', ' công nghệ cubesat', ' công nghệ truyền thông vệ tinh', ' công nghệ quan sát Trái Đất', ' công nghệ thời tiết số', ' công nghệ dự báo thời tiết', ' công nghệ mô phỏng khí hậu', ' công nghệ phân tích môi trường', ' công nghệ giám sát môi trường', ' công nghệ IoT môi trường', ' công nghệ cảm biến môi trường', ' công nghệ phân tích chất lượng không khí', ' công nghệ phân tích chất lượng nước', ' công nghệ quản lý tài nguyên nước', ' công nghệ tưới tiêu thông minh', ' công nghệ nông nghiệp chính xác', ' công nghệ nông nghiệp thông minh', ' công nghệ nông nghiệp thẳng đứng', ' công nghệ thủy canh', ' công nghệ khí canh', ' công nghệ đất thông minh', ' công nghệ cảm biến đất', ' công nghệ phân tích đất', ' công nghệ phân bón thông minh', ' công nghệ thuốc trừ sâu sinh học', ' công nghệ kiểm soát côn trùng', ' công nghệ nông nghiệp hữu cơ', ' công nghệ nông nghiệp tái sinh', ' công nghệ chăn nuôi thông minh', ' công nghệ nuôi trồng thủy sản', ' công nghệ nuôi trồng tảo', ' công nghệ thực phẩm bền vững', ' công nghệ thực phẩm nhân tạo', ' công nghệ thịt nuôi cấy', ' công nghệ protein thay thế', ' công nghệ thực phẩm in 3D', ' công nghệ đóng gói thông minh', ' công nghệ bảo quản thực phẩm', ' công nghệ chuỗi cung ứng lạnh', ' công nghệ truy xuất nguồn gốc thực phẩm', ' công nghệ blockchain thực phẩm', ' công nghệ IoT thực phẩm', ' công nghệ phân tích thực phẩm', ' công nghệ kiểm tra an toàn thực phẩm', ' công nghệ tiêu chuẩn thực phẩm', ' công nghệ HACCP', ' công nghệ ISO 22000', ' công nghệ sản xuất thực phẩm', ' công nghệ chế biến thực phẩm', ' công nghệ tự động hóa thực phẩm', ' công nghệ robot nhà bếp', ' công nghệ nhà hàng thông minh', ' công nghệ đặt món trực tuyến', ' công nghệ giao đồ ăn', ' công nghệ ứng dụng giao đồ ăn', ' công nghệ thanh toán không tiếp xúc', ' công nghệ thanh toán di động', ' công nghệ ví điện tử', ' công nghệ ngân hàng số', ' công nghệ fintech', ' công nghệ ngân hàng mở', ' công nghệ API ngân hàng', ' công nghệ tài chính cá nhân', ' công nghệ quản lý tài sản', ' công nghệ đầu tư tự động', ' công nghệ robo-advisor', ' công nghệ giao dịch chứng khoán', ' công nghệ giao dịch tiền điện tử', ' công nghệ sàn giao dịch phi tập trung', ' công nghệ ví tiền điện tử', ' công nghệ staking tiền điện tử', ' công nghệ yield farming', ' công nghệ lending tiền điện tử', ' công nghệ stablecoin', ' công nghệ CBDC', ' công nghệ tiền kỹ thuật số', ' công nghệ blockchain tài chính', ' công nghệ bảo hiểm số', ' công nghệ insurtech', ' công nghệ phân tích rủi ro bảo hiểm', ' công nghệ bảo hiểm vi mô', ' công nghệ bảo hiểm theo yêu cầu', ' công nghệ hợp đồng bảo hiểm thông minh', ' công nghệ phân tích dữ liệu bảo hiểm', ' công nghệ chăm sóc khách hàng', ' công nghệ CRM', ' công nghệ ERP', ' công nghệ quản lý doanh nghiệp', ' công nghệ quản lý nhân sự', ' công nghệ tuyển dụng trực tuyến', ' công nghệ học trực tuyến', ' công nghệ giáo dục số', ' công nghệ lớp học ảo', ' công nghệ thực tế ảo giáo dục', ' công nghệ gamification giáo dục', ' công nghệ học cá nhân hóa', ' công nghệ AI giáo dục', ' công nghệ phân tích học tập', ' công nghệ học tập thích nghi', ' công nghệ MOOC', ' công nghệ khóa học trực tuyến', ' công nghệ nền tảng học trực tuyến', ' công nghệ công cụ học trực tuyến', ' công nghệ Zoom', ' công nghệ Microsoft Teams', ' công nghệ Google Classroom', ' công nghệ công cụ họp trực tuyến', ' công nghệ hội nghị truyền hình', ' công nghệ làm việc từ xa', ' công nghệ văn phòng số', ' công nghệ công cụ cộng tác', ' công nghệ quản lý dự án', ' công nghệ Trello', ' công nghệ Asana', ' công nghệ Jira', ' công nghệ Slack', ' công nghệ công cụ giao tiếp', ' công nghệ bảo mật giao tiếp', ' công nghệ mã hóa giao tiếp', ' công nghệ lưu trữ tài liệu', ' công nghệ Google Drive', ' công nghệ Dropbox', ' công nghệ OneDrive', ' công nghệ quản lý tài liệu', ' công nghệ chữ ký điện tử', ' công nghệ hợp đồng điện tử', ' công nghệ tự động hóa văn phòng', ' công nghệ RPA', ' công nghệ tự động hóa quy trình', ' công nghệ quy trình kinh doanh', ' công nghệ quản lý quy trình', ' công nghệ BPM', ' công nghệ phân tích quy trình', ' công nghệ tối ưu hóa quy trình', ' công nghệ chuyển đổi số', ' công nghệ công nghiệp 4.0', ' công nghệ sản xuất thông minh', ' công nghệ nhà máy thông minh', ' công nghệ tự động hóa nhà máy', ' công nghệ robot sản xuất', ' công nghệ IoT sản xuất', ' công nghệ cảm biến sản xuất', ' công nghệ phân tích sản xuất', ' công nghệ bảo trì dự đoán', ' công nghệ quản lý tài sản', ' công nghệ EAM', ' công nghệ CMMS', ' công nghệ quản lý vòng đời sản phẩm', ' công nghệ PLM', ' công nghệ thiết kế sản phẩm', ' công nghệ CAD', ' công nghệ CAM', ' công nghệ CAE', ' công nghệ mô phỏng sản phẩm', ' công nghệ thực tế ảo sản phẩm', ' công nghệ bản sao số', ' công nghệ digital twin', ' công nghệ mô phỏng số', ' công nghệ phân tích số', ' công nghệ tối ưu hóa số', ' công nghệ phân tích hiệu suất', ' công nghệ phân tích tài sản', ' công nghệ phân tích năng lượng', ' công nghệ tối ưu hóa năng lượng', ' công nghệ quản lý năng lượng', ' công nghệ EMS', ' công nghệ tòa nhà thông minh', ' công nghệ BMS', ' công nghệ quản lý tòa nhà', ' công nghệ cảm biến tòa nhà', ' công nghệ phân tích tòa nhà', ' công nghệ bảo mật tòa nhà', ' công nghệ an ninh tòa nhà', ' công nghệ camera thông minh', ' công nghệ nhận diện biển số', ' công nghệ kiểm soát ra vào', ' công nghệ thẻ thông minh', ' công nghệ IoT tòa nhà', ' công nghệ phân tích không gian', ' công nghệ tối ưu hóa không gian', ' công nghệ quản lý không gian', ' công nghệ thiết kế nội thất', ' công nghệ nội thất thông minh', ' công nghệ nội thất bền vững', ' công nghệ vật liệu nội thất', ' công nghệ thời trang thông minh', ' công nghệ thời trang bền vững', ' công nghệ tái chế thời trang', ' công nghệ vải thông minh', ' công nghệ vải bền vững', ' công nghệ may mặc thông minh', ' công nghệ thiết kế thời trang', ' công nghệ phần mềm thiết kế', ' công nghệ Adobe Illustrator', ' công nghệ Adobe Photoshop', ' công nghệ Canva', ' công nghệ thiết kế đồ họa', ' công nghệ thiết kế UI/UX', ' công nghệ trải nghiệm người dùng', ' công nghệ thiết kế giao diện', ' công nghệ thiết kế sản phẩm', ' công nghệ thiết kế công nghiệp', ' công nghệ thiết kế bền vững', ' công nghệ thiết kế sinh thái', ' công nghệ kiến trúc thông minh', ' công nghệ kiến trúc bền vững', ' công nghệ BIM', ' công nghệ mô phỏng kiến trúc', ' công nghệ thiết kế đô thị', ' công nghệ quy hoạch đô thị', ' công nghệ đô thị thông minh', ' công nghệ giao thông đô thị', ' công nghệ xe đạp chia sẻ', ' công nghệ xe điện chia sẻ', ' công nghệ phương tiện công cộng', ' công nghệ giao thông công cộng', ' công nghệ quản lý giao thông', ' công nghệ ITS', ' công nghệ phân tích giao thông', ' công nghệ tối ưu hóa giao thông', ' công nghệ bản đồ giao thông', ' công nghệ định tuyến thông minh', ' công nghệ định tuyến thời gian thực', ' công nghệ xe tự hành đô thị', ' công nghệ xe điện đô thị', ' công nghệ pin xe điện', ' công nghệ sạc xe điện', ' công nghệ trạm sạc xe điện', ' công nghệ lưới sạc xe điện', ' công nghệ năng lượng xe điện', ' công nghệ xe hydro', ' công nghệ xe tự hành cấp 4', ' công nghệ xe tự hành cấp 5', ' công nghệ cảm biến xe tự hành', ' công nghệ lidar xe tự hành', ' công nghệ radar xe tự hành', ' công nghệ camera xe tự hành', ' công nghệ AI xe tự hành', ' công nghệ phân tích giao thông', ' công nghệ an toàn giao thông', ' công nghệ giám sát giao thông', ' công nghệ phân tích tai nạn', ' công nghệ quản lý tai nạn', ' công nghệ cứu hộ giao thông', ' công nghệ y tế giao thông', ' công nghệ sơ cứu', ' công nghệ y tế khẩn cấp', ' công nghệ xe cứu thương thông minh', ' công nghệ IoT y tế', ' công nghệ cảm biến y tế', ' công nghệ thiết bị y tế', ' công nghệ thiết bị đeo y tế', ' công nghệ đồng hồ thông minh', ' công nghệ vòng đeo sức khỏe', ' công nghệ theo dõi sức khỏe', ' công nghệ phân tích sức khỏe', ' công nghệ y học cá nhân hóa', ' công nghệ y học chính xác', ' công nghệ di truyền học', ' công nghệ chỉnh sửa gen', ' công nghệ CRISPR', ' công nghệ sinh học tổng hợp', ' công nghệ sinh học y tế', ' công nghệ sinh học nông nghiệp', ' công nghệ sinh học môi trường', ' công nghệ vi sinh vật học', ' công nghệ công nghệ sinh học biển', ' công nghệ nuôi cấy mô', ' công nghệ tế bào gốc', ' công nghệ liệu pháp gen', ' công nghệ vắc-xin mRNA', ' công nghệ vắc-xin công nghệ cao', ' công nghệ sản xuất vắc-xin', ' công nghệ phân phối vắc-xin', ' công nghệ chuỗi cung ứng vắc-xin', ' công nghệ y tế từ xa', ' công nghệ telemedicine', ' công nghệ tư vấn y tế trực tuyến', ' công nghệ hồ sơ y tế điện tử', ' công nghệ EMR', ' công nghệ EHR', ' công nghệ quản lý bệnh viện', ' công nghệ phân tích bệnh viện', ' công nghệ tối ưu hóa bệnh viện', ' công nghệ robot phẫu thuật', ' công nghệ phẫu thuật từ xa', ' công nghệ phẫu thuật nội soi', ' công nghệ phẫu thuật laser', ' công nghệ chẩn đoán hình ảnh', ' công nghệ AI chẩn đoán', ' công nghệ phân tích hình ảnh y tế', ' công nghệ X-quang số', ' công nghệ MRI', ' công nghệ CT scan', ' công nghệ siêu âm', ' công nghệ cảm biến y tế', ' công nghệ thiết bị y tế thông minh', ' công nghệ IoT bệnh viện', ' công nghệ phân tích dữ liệu y tế', ' công nghệ big data y tế', ' công nghệ phân tích bệnh nhân', ' công nghệ dự đoán bệnh', ' công nghệ quản lý bệnh mãn tính', ' công nghệ chăm sóc sức khỏe tại nhà', ' công nghệ chăm sóc người cao tuổi', ' công nghệ thiết bị hỗ trợ người cao tuổi', ' công nghệ robot chăm sóc', ' công nghệ nhà thông minh y tế', ' công nghệ cảm biến nhà thông minh', ' công nghệ phân tích nhà thông minh', ' công nghệ an ninh nhà thông minh', ' công nghệ chiếu sáng thông minh', ' công nghệ điều hòa thông minh', ' công nghệ thiết bị gia dụng thông minh', ' công nghệ IoT gia đình', ' công nghệ cảm biến gia đình', ' công nghệ quản lý năng lượng gia đình', ' công nghệ tối ưu hóa năng lượng gia đình', ' công nghệ năng lượng mặt trời gia đình', ' công nghệ pin lưu trữ gia đình', ' công nghệ lưới điện gia đình', ' công nghệ nhà thông minh bền vững', ' công nghệ tái chế tại nhà', ' công nghệ quản lý rác thải', ' công nghệ tái chế rác thải', ' công nghệ phân loại rác thải', ' công nghệ IoT rác thải', ' công nghệ cảm biến rác thải', ' công nghệ quản lý môi trường đô thị', ' công nghệ giám sát môi trường đô thị', ' công nghệ phân tích môi trường đô thị', ' công nghệ chất lượng không khí đô thị', ' công nghệ chất lượng nước đô thị', ' công nghệ quản lý tài nguyên đô thị', ' công nghệ tái chế đô thị', ' công nghệ kinh tế tuần hoàn đô thị', ' công nghệ phát triển bền vững đô thị', ' công nghệ carbon neutral đô thị', ' công nghệ giảm phát thải đô thị', ' công nghệ năng lượng tái tạo đô thị', ' công nghệ năng lượng mặt trời đô thị', ' công nghệ năng lượng gió đô thị', ' công nghệ năng lượng hydro đô thị', ' công nghệ lưu trữ năng lượng đô thị', ' công nghệ lưới điện thông minh đô thị', ' công nghệ quản lý năng lượng đô thị', ' công nghệ tối ưu hóa năng lượng đô thị', ' công nghệ giao thông xanh đô thị', ' công nghệ xe điện đô thị', ' công nghệ xe hydro đô thị', ' công nghệ phương tiện xanh đô thị', ' công nghệ cơ sở hạ tầng xanh đô thị', ' công nghệ tòa nhà xanh đô thị', ' công nghệ công viên đô thị', ' công nghệ không gian xanh đô thị', ' công nghệ nông nghiệp đô thị', ' công nghệ nông nghiệp thẳng đứng đô thị', ' công nghệ thủy canh đô thị', ' công nghệ khí canh đô thị', ' công nghệ thực phẩm đô thị', ' công nghệ thực phẩm bền vững đô thị', ' công nghệ chuỗi cung ứng thực phẩm đô thị', ' công nghệ truy xuất nguồn gốc thực phẩm đô thị', ' công nghệ blockchain thực phẩm đô thị', ' công nghệ IoT thực phẩm đô thị', ' công nghệ phân tích thực phẩm đô thị', ' công nghệ an toàn thực phẩm đô thị', ' công nghệ tiêu chuẩn thực phẩm đô thị', ' công nghệ sản xuất thực phẩm đô thị', ' công nghệ chế biến thực phẩm đô thị', ' công nghệ tự động hóa thực phẩm đô thị', ' công nghệ nhà hàng thông minh đô thị', ' công nghệ giao đồ ăn đô thị', ' công nghệ ứng dụng giao đồ ăn đô thị', ' công nghệ thanh toán không tiếp xúc đô thị', ' công nghệ thanh toán di động đô thị', ' công nghệ ví điện tử đô thị', ' công nghệ ngân hàng số đô thị', ' công nghệ fintech đô thị', ' công nghệ ngân hàng mở đô thị', ' công nghệ tài chính cá nhân đô thị', ' công nghệ quản lý tài sản đô thị', ' công nghệ đầu tư tự động đô thị', ' công nghệ robo-advisor đô thị', ' công nghệ giao dịch chứng khoán đô thị', ' công nghệ giao dịch tiền điện tử đô thị', ' công nghệ sàn giao dịch phi tập trung đô thị', ' công nghệ ví tiền điện tử đô thị', ' công nghệ staking tiền điện tử đô thị', ' công nghệ yield farming đô thị', ' công nghệ lending tiền điện tử đô thị', ' công nghệ stablecoin đô thị', ' công nghệ CBDC đô thị', ' công nghệ tiền kỹ thuật số đô thị', ' công nghệ blockchain tài chính đô thị', ' công nghệ bảo hiểm số đô thị', ' công nghệ insurtech đô thị', ' công nghệ phân tích rủi ro bảo hiểm đô thị', ' công nghệ bảo hiểm vi mô đô thị', ' công nghệ bảo hiểm theo yêu cầu đô thị', ' công nghệ hợp đồng bảo hiểm thông minh đô thị', ' công nghệ phân tích dữ liệu bảo hiểm đô thị', ' công nghệ chăm sóc khách hàng đô thị', ' công nghệ CRM đô thị', ' công nghệ ERP đô thị', ' công nghệ quản lý doanh nghiệp đô thị', ' công nghệ quản lý nhân sự đô thị', ' công nghệ tuyển dụng trực tuyến đô thị', ' công nghệ học trực tuyến đô thị', ' công nghệ giáo dục số đô thị', ' công nghệ lớp học ảo đô thị', ' công nghệ thực tế ảo giáo dục đô thị', ' công nghệ gamification giáo dục đô thị', ' công nghệ học cá nhân hóa đô thị', ' công nghệ AI giáo dục đô thị', ' công nghệ phân tích học tập đô thị', ' công nghệ học tập thích nghi đô thị', ' công nghệ MOOC đô thị', ' công nghệ khóa học trực tuyến đô thị', ' công nghệ nền tảng học trực tuyến đô thị', ' công nghệ công cụ học trực tuyến đô thị', ' công nghệ Zoom đô thị', ' công nghệ Microsoft Teams đô thị', ' công nghệ Google Classroom đô thị', ' công nghệ công cụ họp trực tuyến đô thị', ' công nghệ hội nghị truyền hình đô thị', ' công nghệ làm việc từ xa đô thị', ' công nghệ văn phòng số đô thị', ' công nghệ công cụ cộng tác đô thị', ' công nghệ quản lý dự án đô thị', ' công nghệ Trello đô thị', ' công nghệ Asana đô thị', ' công nghệ Jira đô thị', ' công nghệ Slack đô thị', ' công nghệ công cụ giao tiếp đô thị', ' công nghệ bảo mật giao tiếp đô thị', ' công nghệ mã hóa giao tiếp đô thị', ' công nghệ lưu trữ tài liệu đô thị', ' công nghệ Google Drive đô thị', ' công nghệ Dropbox đô thị', ' công nghệ OneDrive đô thị', ' công nghệ quản lý tài liệu đô thị', ' công nghệ chữ ký điện tử đô thị', ' công nghệ hợp đồng điện tử đô thị', ' công nghệ tự động hóa văn phòng đô thị', ' công nghệ RPA đô thị', ' công nghệ tự động hóa quy trình đô thị', ' công nghệ quy trình kinh doanh đô thị', ' công nghệ quản lý quy trình đô thị', ' công nghệ BPM đô thị', ' công nghệ phân tích quy trình đô thị', ' công nghệ tối ưu hóa quy trình đô thị', ' công nghệ chuyển đổi số đô thị', ' công nghệ công nghiệp 4.0 đô thị', ' công nghệ sản xuất thông minh đô thị', ' công nghệ nhà máy thông minh đô thị', ' công nghệ tự động hóa nhà máy đô thị', ' công nghệ robot sản xuất đô thị', ' công nghệ IoT sản xuất đô thị', ' công nghệ cảm biến sản xuất đô thị', ' công nghệ phân tích sản xuất đô thị', ' công nghệ bảo trì dự đoán đô thị', ' công nghệ quản lý tài sản đô thị', ' công nghệ EAM đô thị', ' công nghệ CMMS đô thị', ' công nghệ quản lý vòng đời sản phẩm đô thị', ' công nghệ PLM đô thị', ' công nghệ thiết kế sản phẩm đô thị', ' công nghệ CAD đô thị', ' công nghệ CAM đô thị', ' công nghệ CAE đô thị', ' công nghệ mô phỏng sản phẩm đô thị', ' công nghệ thực tế ảo sản phẩm đô thị', ' công nghệ bản sao số đô thị', ' công nghệ digital twin đô thị', ' công nghệ mô phỏng số đô thị', ' công nghệ phân tích số đô thị', ' công nghệ tối ưu hóa số đô thị', ' công nghệ phân tích hiệu suất đô thị', ' công nghệ phân tích tài sản đô thị', ' công nghệ phân tích năng lượng đô thị', ' công nghệ tối ưu hóa năng lượng đô thị', ' công nghệ quản lý năng lượng đô thị', ' công nghệ EMS đô thị', ' công nghệ tòa nhà thông minh đô thị', ' công nghệ BMS đô thị', ' công nghệ quản lý tòa nhà đô thị', ' công nghệ cảm biến tòa nhà đô thị', ' công nghệ phân tích tòa nhà đô thị', ' công nghệ bảo mật tòa nhà đô thị', ' công nghệ an ninh tòa nhà đô thị', ' công nghệ camera thông minh đô thị', ' công nghệ nhận diện biển số đô thị', ' công nghệ kiểm soát ra vào đô thị', ' công nghệ thẻ thông minh đô thị', ' công nghệ IoT tòa nhà đô thị', ' công nghệ phân tích không gian đô thị', ' công nghệ tối ưu hóa không gian đô thị', ' công nghệ quản lý không gian đô thị', ' công nghệ thiết kế nội thất đô thị', ' công nghệ nội thất thông minh đô thị', ' công nghệ nội thất bền vững đô thị', ' công nghệ vật liệu nội thất đô thị', ' công nghệ thời trang thông minh đô thị', ' công nghệ thời trang bền vững đô thị', ' công nghệ tái chế thời trang đô thị', ' công nghệ vải thông minh đô thị', ' công nghệ vải bền vững đô thị', ' công nghệ may mặc thông minh đô thị', ' công nghệ thiết kế thời trang đô thị', ' công nghệ phần mềm thiết kế đô thị', ' công nghệ Adobe Illustrator đô thị', ' công nghệ Adobe Photoshop đô thị', ' công nghệ Canva đô thị', ' công nghệ thiết kế đồ họa đô thị', ' công nghệ thiết kế UI/UX đô thị', ' công nghệ trải nghiệm người dùng đô thị', ' công nghệ thiết kế giao diện đô thị', ' công nghệ thiết kế sản phẩm đô thị', ' công nghệ thiết kế công nghiệp đô thị', ' công nghệ thiết kế bền vững đô thị', ' công nghệ thiết kế sinh thái đô thị', ' công nghệ kiến trúc thông minh đô thị', ' công nghệ kiến trúc bền vững đô thị', ' công nghệ BIM đô thị', ' công nghệ mô phỏng kiến trúc đô thị', ' công nghệ thiết kế đô thị', ' công nghệ quy hoạch đô thị', ' công nghệ đô thị thông minh', ' công nghệ giao thông đô thị', ' công nghệ xe đạp chia sẻ đô thị', ' công nghệ xe điện chia sẻ đô thị', ' công nghệ phương tiện công cộng đô thị', ' công nghệ giao thông công cộng đô thị', ' công nghệ quản lý giao thông đô thị', ' công nghệ ITS đô thị', ' công nghệ phân tích giao thông đô thị', ' công nghệ tối ưu hóa giao thông đô thị', ' công nghệ bản đồ giao thông đô thị', ' công nghệ định tuyến thông minh đô thị', ' công nghệ định tuyến thời gian thực đô thị', ' công nghệ xe tự hành đô thị', ' công nghệ xe điện đô thị', ' công nghệ pin xe điện đô thị', ' công nghệ sạc xe điện đô thị', ' công nghệ trạm sạc xe điện đô thị', ' công nghệ lưới sạc xe điện đô thị', ' công nghệ năng lượng xe điện đô thị', ' công nghệ xe hydro đô thị', ' công nghệ xe tự hành cấp 4 đô thị', ' công nghệ xe tự hành cấp 5 đô thị', ' công nghệ cảm biến xe tự hành đô thị', ' công nghệ lidar xe tự hành đô thị', ' công nghệ radar xe tự hành đô thị', ' công nghệ camera xe tự hành đô thị', ' công nghệ AI xe tự hành đô thị', ' công nghệ phân tích giao thông đô thị', ' công nghệ an toàn giao thông đô thị', ' công nghệ giám sát giao thông đô thị', ' công nghệ phân tích tai nạn đô thị', ' công nghệ quản lý tai nạn đô thị', ' công nghệ cứu hộ giao thông đô thị', ' công nghệ y tế giao thông đô thị', ' công nghệ sơ cứu đô thị', ' công nghệ y tế khẩn cấp đô thị', ' công nghệ xe cứu thương thông minh đô thị', ' công nghệ IoT y tế đô thị', ' công nghệ cảm biến y tế đô thị', ' công nghệ thiết bị y tế đô thị', ' công nghệ thiết bị đeo y tế đô thị', ' công nghệ đồng hồ thông minh đô thị', ' công nghệ vòng đeo sức khỏe đô thị', ' công nghệ theo dõi sức khỏe đô thị', ' công nghệ phân tích sức khỏe đô thị', ' công nghệ y học cá nhân hóa đô thị', ' công nghệ y học chính xác đô thị', ' công nghệ di truyền học đô thị', ' công nghệ chỉnh sửa gen đô thị', ' công nghệ CRISPR đô thị', ' công nghệ sinh học tổng hợp đô thị', ' công nghệ sinh học y tế đô thị', ' công nghệ sinh học nông nghiệp đô thị', ' công nghệ sinh học môi trường đô thị', ' công nghệ vi sinh vật học đô thị', ' công nghệ công nghệ sinh học biển đô thị', ' công nghệ nuôi cấy mô đô thị', ' công nghệ tế bào gốc đô thị', ' công nghệ liệu pháp gen đô thị', ' công nghệ vắc-xin mRNA đô thị', ' công nghệ vắc-xin công nghệ cao đô thị', ' công nghệ sản xuất vắc-xin đô thị', ' công nghệ phân phối vắc-xin đô thị', ' công nghệ chuỗi cung ứng vắc-xin đô thị', ' công nghệ y tế từ xa đô thị', ' công nghệ telemedicine đô thị', ' công nghệ tư vấn y tế trực tuyến đô thị', ' công nghệ hồ sơ y tế điện tử đô thị', ' công nghệ EMR đô thị', ' công nghệ EHR đô thị', ' công nghệ quản lý bệnh viện đô thị', ' công nghệ phân tích bệnh viện đô thị', ' công nghệ tối ưu hóa bệnh viện đô thị', ' công nghệ robot phẫu thuật đô thị', ' công nghệ phẫu thuật từ xa đô thị', ' công nghệ phẫu thuật nội soi đô thị', ' công nghệ phẫu thuật laser đô thị', ' công nghệ chẩn đoán hình ảnh đô thị', ' công nghệ AI chẩn đoán đô thị', ' công nghệ phân tích hình ảnh y tế đô thị', ' công nghệ X-quang số đô thị', ' công nghệ MRI đô thị', ' công nghệ CT scan đô thị', ' công nghệ siêu âm đô thị', ' công nghệ cảm biến y tế đô thị', ' công nghệ thiết bị y tế thông minh đô thị', ' công nghệ IoT bệnh viện đô thị', ' công nghệ phân tích dữ liệu y tế đô thị', ' công nghệ big data y tế đô thị', ' công nghệ phân tích bệnh nhân đô thị', ' công nghệ dự đoán bệnh đô thị', ' công nghệ quản lý bệnh mãn tính đô thị', ' công nghệ chăm sóc sức khỏe tại nhà đô thị', ' công nghệ chăm sóc người cao tuổi đô thị', ' công nghệ thiết bị hỗ trợ người cao tuổi đô thị', ' công nghệ robot chăm sóc đô thị', ' công nghệ nhà thông minh y tế đô thị', ' công nghệ cảm biến nhà thông minh đô thị', ' công nghệ phân tích nhà thông minh đô thị', ' công nghệ an ninh nhà thông minh đô thị', ' công nghệ chiếu sáng thông minh đô thị', ' công nghệ điều hòa thông minh đô thị', ' công nghệ thiết bị gia dụng thông minh đô thị', ' công nghệ IoT gia đình đô thị', ' công nghệ cảm biến gia đình đô thị', ' công nghệ quản lý năng lượng gia đình đô thị', ' công nghệ tối ưu hóa năng lượng gia đình đô thị', ' công nghệ năng lượng mặt trời gia đình đô thị', ' công nghệ pin lưu trữ gia đình đô thị', ' công nghệ lưới điện gia đình đô thị', ' công nghệ nhà thông minh bền vững đô thị', ' công nghệ tái chế tại nhà đô thị', ' công nghệ quản lý rác thải đô thị', ' công nghệ tái chế rác thải đô thị', ' công nghệ phân loại rác thải đô thị', ' công nghệ IoT rác thải đô thị', ' công nghệ cảm biến rác thải đô thị', ' công nghệ quản lý môi trường đô thị', ' công nghệ giám sát môi trường đô thị', ' công nghệ phân tích môi trường đô thị', ' công nghệ chất lượng không khí đô thị', ' công nghệ chất lượng nước đô thị', ' công nghệ quản lý tài nguyên đô thị', ' công nghệ tái chế đô thị', ' công nghệ kinh tế tuần hoàn đô thị', ' công nghệ phát triển bền vững đô thị', ' công nghệ carbon neutral đô thị', ' công nghệ giảm phát thải đô thị', ' công nghệ năng lượng tái tạo đô thị', ' công nghệ năng lượng mặt trời đô thị', ' công nghệ năng lượng gió đô thị', ' công nghệ năng lượng hydro đô thị', ' công nghệ lưu trữ năng lượng đô thị', ' công nghệ lưới điện thông minh đô thị', ' công nghệ quản lý năng lượng đô thị', ' công nghệ tối ưu hóa năng lượng đô thị', ' công nghệ giao thông xanh đô thị', ' công nghệ xe điện đô thị', ' công nghệ xe hydro đô thị', ' công nghệ phương tiện xanh đô thị', ' công nghệ cơ sở hạ tầng xanh đô thị', ' công nghệ tòa nhà xanh đô thị', ' công nghệ công viên đô thị', ' công nghệ không gian xanh đô thị', ' công nghệ nông nghiệp đô thị', ' công nghệ nông nghiệp thẳng đứng đô thị', ' công nghệ thủy canh đô thị', ' công nghệ khí canh đô thị', ' công nghệ thực phẩm đô thị', ' công nghệ thực phẩm bền vững đô thị', ' công nghệ chuỗi cung ứng thực phẩm đô thị', ' công nghệ truy xuất nguồn gốc thực phẩm đô thị', ' công nghệ blockchain thực phẩm đô thị', ' công nghệ IoT thực phẩm đô thị', ' công nghệ phân tích thực phẩm đô thị', ' công nghệ an toàn thực phẩm đô thị', ' công nghệ tiêu chuẩn thực phẩm đô thị', ' công nghệ sản xuất thực phẩm đô thị', ' công nghệ chế biến thực phẩm đô thị', ' công nghệ tự động hóa thực phẩm đô thị', ' công nghệ nhà hàng thông minh đô thị', ' công nghệ giao đồ ăn đô thị', ' công nghệ ứng dụng giao đồ ăn đô thị', ' công nghệ thanh toán không tiếp xúc đô thị', ' công nghệ thanh toán di động đô thị', ' công nghệ ví điện tử đô thị', ' công nghệ ngân hàng số đô thị', ' công nghệ fintech đô thị', ' công nghệ ngân hàng mở đô thị', ' công nghệ tài chính cá nhân đô thị', ' công nghệ quản lý tài sản đô thị', ' công nghệ đầu tư tự động đô thị', ' công nghệ robo-advisor đô thị', ' công nghệ giao dịch chứng khoán đô thị', ' công nghệ giao dịch tiền điện tử đô thị', ' công nghệ sàn giao dịch phi tập trung đô thị', ' công nghệ ví tiền điện tử đô thị', ' công nghệ staking tiền điện tử đô thị', ' công nghệ yield farming đô thị', ' công nghệ lending tiền điện tử đô thị', ' công technology stablecoin đô thị', ' công nghệ CBDC đô thị', ' công nghệ tiền kỹ thuật số đô thị', ' công nghệ blockchain tài chính đô thị', ' công nghệ bảo hiểm số đô thị', ' công nghệ insurtech đô thị', ' công nghệ phân tích rủi ro bảo hiểm đô thị', ' công nghệ bảo hiểm vi mô đô thị', ' công nghệ bảo hiểm theo yêu cầu đô thị', ' công nghệ hợp đồng bảo hiểm thông minh đô thị', ' công nghệ phân tích dữ liệu bảo hiểm đô thị', ' công nghệ chăm sóc khách hàng đô thị', ' công nghệ CRM đô thị', ' công nghệ ERP đô thị', ' công nghệ quản lý doanh nghiệp đô thị', ' công nghệ quản lý nhân sự đô thị', ' công nghệ tuyển dụng trực tuyến đô thị', ' công nghệ học trực tuyến đô thị', ' công nghệ giáo dục số đô thị', ' công nghệ lớp học ảo đô thị', ' công nghệ thực tế ảo giáo dục đô thị', ' công nghệ gamification giáo dục đô thị', ' công nghệ học cá nhân hóa đô thị', ' công nghệ AI giáo dục đô thị', ' công nghệ phân tích học tập đô thị', ' công nghệ học tập thích nghi đô thị', ' công nghệ MOOC đô thị', ' công nghệ khóa học trực tuyến đô thị', ' công nghệ nền tảng học trực tuyến đô thị', ' công nghệ công cụ học trực tuyến đô thị', ' công nghệ Zoom đô thị', ' công nghệ Microsoft Teams đô thị', ' công nghệ Google Classroom đô thị', ' công nghệ công cụ họp trực tuyến đô thị', ' công nghệ hội nghị truyền hình đô thị', ' công nghệ làm việc từ xa đô thị', ' công nghệ văn phòng số đô thị', ' công nghệ công cụ cộng tác đô thị', ' công nghệ quản lý dự án đô thị', ' công nghệ Trello đô thị', ' công nghệ Asana đô thị', ' công nghệ Jira đô thị', ' công nghệ Slack đô thị', ' công nghệ công cụ giao tiếp đô thị', ' công nghệ bảo mật giao tiếp đô thị', ' công nghệ mã hóa giao tiếp đô thị', ' công nghệ lưu trữ tài liệu đô thị', ' công nghệ Google Drive đô thị', ' công nghệ Dropbox đô thị', ' công nghệ OneDrive đô thị', ' công nghệ quản lý tài liệu đô thị', ' công nghệ chữ ký điện tử đô thị', ' công nghệ hợp đồng điện tử đô thị', ' công nghệ tự động hóa văn phòng đô thị', ' công nghệ RPA đô thị', ' công nghệ tự động hóa quy trình đô thị', ' công nghệ quy trình kinh doanh đô thị', ' công nghệ quản lý quy trình đô thị', ' công nghệ BPM đô thị', ' công nghệ phân tích quy trình đô thị', ' công nghệ tối ưu hóa quy trình đô thị', ' công nghệ chuyển đổi số đô thị', ' công nghệ công nghiệp 4.0 đô thị', ' công nghệ sản xuất thông minh đô thị', ' công nghệ nhà máy thông minh đô thị', ' công nghệ tự động hóa nhà máy đô thị', ' công nghệ robot sản xuất đô thị', ' công nghệ IoT sản xuất đô thị', ' công nghệ cảm biến sản xuất đô thị', ' công nghệ phân tích sản xuất đô thị', ' công nghệ bảo trì dự đoán đô thị', ' công nghệ quản lý tài sản đô thị', ' công nghệ EAM đô thị', ' công nghệ CMMS đô thị', ' công nghệ quản lý vòng đời sản phẩm đô thị', ' công nghệ PLM đô thị', ' công nghệ thiết kế sản phẩm đô thị', ' công nghệ CAD đô thị', ' công nghệ CAM đô thị', ' công nghệ CAE đô thị', ' công nghệ mô phỏng sản phẩm đô thị', ' công nghệ thực tế ảo sản phẩm đô thị', ' công nghệ bản sao số đô thị', ' công nghệ digital twin đô thị', ' công nghệ mô phỏng số đô thị', ' công nghệ phân tích số đô thị', ' công nghệ tối ưu hóa số đô thị', ' công nghệ phân tích hiệu suất đô thị', ' công nghệ phân tích tài sản đô thị', ' công nghệ phân tích năng lượng đô thị', ' công nghệ tối ưu hóa năng lượng đô thị', ' công nghệ quản lý năng lượng đô thị', ' công nghệ EMS đô thị', ' công nghệ tòa nhà thông minh đô thị', ' công nghệ BMS đô thị', ' công nghệ quản lý tòa nhà đô thị', ' công nghệ cảm biến tòa nhà đô thị', ' công nghệ phân tích tòa nhà đô thị', ' công nghệ bảo mật tòa nhà đô thị', ' công nghệ an ninh tòa nhà đô thị', ' công nghệ camera thông minh đô thị', ' công nghệ nhận diện biển số đô thị', ' công nghệ kiểm soát ra vào đô thị', ' công nghệ thẻ thông minh đô thị', ' công nghệ IoT tòa nhà đô thị', ' công nghệ phân tích không gian đô thị', ' công nghệ tối ưu hóa không gian đô thị', ' công nghệ quản lý không gian đô thị', ' công nghệ thiết kế nội thất đô thị', ' công nghệ nội thất thông minh đô thị', ' công nghệ nội thất bền vững đô thị', ' công nghệ vật liệu nội thất đô thị', ' công nghệ thời trang thông minh đô thị', ' công nghệ thời trang bền vững đô thị', ' công nghệ tái chế thời trang đô thị', ' công nghệ vải thông minh đô thị', ' công nghệ vải bền vững đô thị', ' công nghệ may mặc thông minh đô thị', ' công nghệ thiết kế thời trang đô thị', ' công nghệ phần mềm thiết kế đô thị', ' công nghệ Adobe Illustrator đô thị', ' công nghệ Adobe Photoshop đô thị', ' công nghệ Canva đô thị', ' công nghệ thiết kế đồ họa đô thị', ' công nghệ thiết kế UI/UX đô thị', ' công nghệ trải nghiệm người dùng đô thị', ' công nghệ thiết kế giao diện đô thị', ' công nghệ thiết kế sản phẩm đô thị', ' công nghệ thiết kế công nghiệp đô thị', ' công nghệ thiết kế bền vững đô thị', ' công nghệ thiết kế sinh thái đô thị', ' công nghệ kiến trúc thông minh đô thị', ' công nghệ kiến trúc bền vững đô thị', ' công nghệ BIM đô thị', ' công nghệ mô phỏng kiến trúc đô thị', ' công nghệ thiết kế đô thị', ' công nghệ quy hoạch đô thị', ' công nghệ đô thị thông minh', ' công nghệ giao thông đô thị', ' công nghệ xe đạp chia sẻ đô thị', ' công nghệ xe điện chia sẻ đô thị', ' công nghệ phương tiện công cộng đô thị', ' công nghệ giao thông công cộng đô thị', ' công nghệ quản lý giao thông đô thị', ' công nghệ ITS đô thị', ' công nghệ phân tích giao thông đô thị', ' công nghệ tối ưu hóa giao thông đô thị', ' công nghệ bản đồ giao thông đô thị', ' công nghệ định tuyến thông minh đô thị', ' công technology định tuyến thời gian thực đô thị', ' công nghệ xe tự hành đô thị', ' công nghệ xe điện đô thị', ' công nghệ pin xe điện đô thị', ' công nghệ sạc xe điện đô thị', ' công nghệ trạm sạc xe điện đô thị', ' công nghệ lưới sạc xe điện đô thị', ' công nghệ năng lượng xe điện đô thị', ' công nghệ xe hydro đô thị', ' công nghệ xe tự hành cấp 4 đô thị', ' công nghệ xe tự hành cấp 5 đô thị', ' công nghệ cảm biến xe tự hành đô thị', ' công nghệ lidar xe tự hành đô thị', ' công technology radar xe tự hành đô thị', ' công nghệ camera xe tự hành đô thị', ' công technology AI xe tự hành đô thị', ' công nghệ phân tích giao thông đô thị', ' công nghệ an toàn giao thông đô thị', ' công technology giám sát giao thông đô thị', ' công technology phân tích tai nạn đô thị', ' công technology quản lý tai nạn đô thị', ' công technology cứu hộ giao thông đô thị', ' công technology y tế giao thông đô thị', ' công technology sơ cứu đô thị', ' công technology y tế khẩn cấp đô thị', ' công technology xe cứu thương thông minh đô thị', ' công technology IoT y tế đô thị', ' công technology cảm biến y tế đô thị', ' công technology thiết bị y tế đô thị', ' công technology thiết bị đeo y tế đô thị', ' công technology đồng hồ thông minh đô thị', ' công technology vòng đeo sức khỏe đô thị', ' công technology theo dõi sức khỏe đô thị', ' công technology phân tích sức khỏe đô thị', ' công technology y học cá nhân hóa đô thị', ' công technology y học chính xác đô thị', ' công technology di truyền học đô thị', ' công technology chỉnh sửa gen đô thị', ' công technology CRISPR đô thị', ' công technology sinh học tổng hợp đô thị', ' công technology sinh học y tế đô thị', ' công technology sinh học nông nghiệp đô thị', ' công technology sinh học môi trường đô thị', ' công technology vi sinh vật học đô thị', ' công technology công nghệ sinh học biển đô thị', ' công technology nuôi cấy mô đô thị', ' công technology tế bào gốc đô thị', ' công technology liệu pháp gen đô thị', ' công technology vắc-xin mRNA đô thị', ' công technology vắc-xin công nghệ cao đô thị', ' công technology sản xuất vắc-xin đô thị', ' công technology phân phối vắc-xin đô thị', ' công technology chuỗi cung ứng vắc-xin đô thị', ' công technology y tế từ xa đô thị', ' công technology telemedicine đô thị', ' công technology tư vấn y tế trực tuyến đô thị', ' công technology hồ sơ y tế điện tử đô thị', ' công technology EMR đô thị', ' công technology EHR đô thị', ' công technology quản lý bệnh viện đô thị', ' công technology phân tích bệnh viện đô thị', ' công technology tối ưu hóa bệnh viện đô thị', ' công technology robot phẫu thuật đô thị', ' công technology phẫu thuật từ xa đô thị', ' công technology phẫu thuật nội soi đô thị', ' công technology phẫu thuật laser đô thị', ' công technology chẩn đoán hình ảnh đô thị', ' công technology AI chẩn đoán đô thị', ' công technology phân tích hình ảnh y tế đô thị', ' công technology X-quang số đô thị', ' công technology MRI đô thị', ' công technology CT scan đô thị', ' công technology siêu âm đô thị', ' công technology cảm biến y tế đô thị', ' công technology thiết bị y tế thông minh đô thị', ' công technology IoT bệnh viện đô thị', ' công technology phân tích dữ liệu y tế đô thị', ' công technology big data y tế đô thị', ' công technology phân tích bệnh nhân đô thị', ' công technology dự đoán bệnh đô thị', ' công technology quản lý bệnh mãn tính đô thị', ' công technology chăm sóc sức khỏe tại nhà đô thị', ' công technology chăm sóc người cao tuổi đô thị', ' công technology thiết bị hỗ trợ người cao tuổi đô thị', ' công technology robot chăm sóc đô thị', ' công technology nhà thông minh y tế đô thị', ' công technology cảm biến nhà thông minh đô thị', ' công technology phân tích nhà thông minh đô thị', ' công technology an ninh nhà thông minh đô thị', ' công technology chiếu sáng thông minh đô thị', ' công technology điều hòa thông minh đô thị', ' công technology thiết bị gia dụng thông minh đô thị', ' công technology IoT gia đình đô thị', ' công technology cảm biến gia đình đô thị', ' công technology quản lý năng lượng gia đình đô thị', ' công technology tối ưu hóa năng lượng gia đình đô thị', ' công technology năng lượng mặt trời gia đình đô thị', ' công technology pin lưu trữ gia đình đô thị', ' công technology lưới điện gia đình đô thị', ' công technology nhà thông minh bền vững đô thị', ' công technology tái chế tại nhà đô thị', ' công technology quản lý rác thải đô thị', ' công technology tái chế rác thải đô thị', ' công technology phân loại rác thải đô thị', ' công technology IoT rác thải đô thị']

# Biến toàn cục để quản lý driver
driver = None

def signal_handler(sig, frame):
    print("\n🛑 Đã nhận tín hiệu hủy (Ctrl+C). Đang đóng trình duyệt...")
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
    print("✅ Chương trình đã thoát.")
    sys.exit(0)

def init_driver():
    print("Đang khởi tạo Edge driver...")
    try:
        service = Service(EDGE_DRIVER_PATH)
        options = webdriver.EdgeOptions()
        options.add_argument("--headless")  # Chạy ở chế độ không giao diện
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Edge(service=service, options=options)
        print("Edge driver khởi tạo thành công!")
        return driver
    except Exception as e:
        print(f"Lỗi khi khởi tạo driver: {str(e)}")
        traceback.print_exc()
        return None

def tick_recaptcha_if_present(driver):
    try:
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'reCAPTCHA')]"))
        )
        driver.switch_to.frame(iframe)
        print("🔍 Tìm thấy reCAPTCHA, đang tick...")
        checkbox = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
        )
        checkbox.click()
        print("✅ Đã tick reCAPTCHA")
        driver.switch_to.default_content()
        time.sleep(2)
    except TimeoutException:
        print("ℹ️ Không có reCAPTCHA trên trang này.")
    except Exception as e:
        print("⚠️ Lỗi khi xử lý reCAPTCHA:")
        traceback.print_exc()



def get_page_hash(driver):
    try:
        return hashlib.sha256(driver.page_source.encode()).hexdigest()
    except Exception as e:
        print(f"Lỗi khi tính hash: {str(e)}")
        return ""

def handle_quiz(driver):
    """Cố gắng hoàn thành quiz bằng cách nhấp vào các tùy chọn ngẫu nhiên"""
    try:
        print("🧩 Phát hiện nhiệm vụ có thể là quiz. Đang cố gắng hoàn thành...")
        # Tìm các nút trả lời (thường là input radio hoặc button)
        answer_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], button.rqOption")
        if answer_buttons:
            # Chọn ngẫu nhiên một tùy chọn
            random.choice(answer_buttons).click()
            print("✅ Đã chọn một tùy chọn ngẫu nhiên.")
            # Tìm nút gửi (nếu có)
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button.wk_button, input[type='submit']")
                submit_button.click()
                print("✅ Đã gửi câu trả lời.")
            except NoSuchElementException:
                print("ℹ️ Không tìm thấy nút gửi, tiếp tục chờ.")
            time.sleep(5)  # Chờ xử lý
        else:
            print("⚠️ Không tìm thấy tùy chọn trả lời. Có thể cần can thiệp thủ công.")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi xử lý quiz: {str(e)}")
        traceback.print_exc()
        return False

def check_daily_sets(driver):
    print("📋 Đang kiểm tra Daily Sets trên trang Rewards...")
    max_attempts = 3  # Số lần thử tối đa để hoàn thành tất cả nhiệm vụ
    attempt = 1

    while attempt <= max_attempts:
        print(f"🔄 Lần thử {attempt}/{max_attempts}...")
        try:
            driver.get(REWARDS_URL)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "m-card-group"))
            )
            print("✅ Đã tải trang Rewards.")

            # Tìm tất cả các thẻ mee-card
            cards = driver.find_elements(By.CSS_SELECTOR, "mee-card")
            print(f"🔍 Tìm thấy {len(cards)} nhiệm vụ Daily Sets.")
            incomplete_tasks = False

            for index, card in enumerate(cards):
                try:
                    # Lấy tiêu đề nhiệm vụ
                    task_title = card.find_element(By.CSS_SELECTOR, "h3.c-heading").text
                    print(f"📌 Nhiệm vụ {index + 1}: {task_title}")

                    # Kiểm tra trạng thái hoàn thành
                    points_div = card.find_element(By.CSS_SELECTOR, "mee-rewards-points .points")
                    try:
                        icon = points_div.find_element(By.CSS_SELECTOR, "span.mee-icon")
                        icon_class = icon.get_attribute("class")
                    except NoSuchElementException:
                        print(f"⚠️ Không tìm thấy biểu tượng trạng thái cho nhiệm vụ '{task_title}'.")
                        incomplete_tasks = True
                        continue

                    if "mee-icon-SkypeCircleCheck" in icon_class:
                        print(f"✅ Nhiệm vụ '{task_title}' đã hoàn thành.")
                        continue

                    if "mee-icon-AddMedium" in icon_class:
                        print(f"⚠️ Nhiệm vụ '{task_title}' chưa hoàn thành. Đang thực hiện...")
                        incomplete_tasks = True
                        # Lấy link nhiệm vụ
                        link_element = card.find_element(By.CSS_SELECTOR, "a.ds-card-sec")
                        task_url = link_element.get_attribute("href")
                        print(f"🔗 Truy cập: {task_url}")

                        # Mở link nhiệm vụ
                        driver.get(task_url)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        print(f"✅ Đã truy cập trang nhiệm vụ.")

                        # Kiểm tra nếu là quiz
                        if "quiz" in task_url.lower():
                            handle_quiz(driver)
                        else:
                            # Chờ lâu hơn để đảm bảo ghi nhận
                            time.sleep(15)

                        # Quay lại trang Rewards
                        driver.get(REWARDS_URL)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "m-card-group"))
                        )
                        print("🔄 Quay lại trang Rewards để kiểm tra.")
                    else:
                        print(f"⚠️ Trạng thái không xác định cho nhiệm vụ '{task_title}'.")
                        incomplete_tasks = True
                except NoSuchElementException as e:
                    print(f"⚠️ Lỗi: Không tìm thấy phần tử cần thiết trong nhiệm vụ {index + 1}: {str(e)}")
                    incomplete_tasks = True
                    continue
                except Exception as e:
                    print(f"❌ Lỗi khi xử lý nhiệm vụ {index + 1}: {str(e)}")
                    traceback.print_exc()
                    incomplete_tasks = True
                    continue

            if not incomplete_tasks:
                print("🎉 Tất cả nhiệm vụ Daily Sets đã hoàn thành!")
                return True
            else:
                print("⚠️ Vẫn còn nhiệm vụ chưa hoàn thành. Thử lại...")
                attempt += 1
                time.sleep(5)  # Nghỉ trước khi thử lại
        except TimeoutException:
            print("❌ Timeout khi tải trang Rewards.")
            attempt += 1
            time.sleep(5)
        except Exception as e:
            print(f"❌ Lỗi khi kiểm tra Daily Sets: {str(e)}")
            traceback.print_exc()
            attempt += 1
            time.sleep(5)

    print("⚠️ Đã hết số lần thử. Có thể cần can thiệp thủ công.")
    return False

def get_hot_keywords():
    cache_file = "hot_keywords.json"
    today = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("date") == today and cache.get("keywords"):
            print("📚 Sử dụng từ khóa hot từ cache hôm nay.")
            return cache["keywords"]

    try:
        print("🌐 Đang lấy từ khóa hot từ Google Trends...")
        pytrends = TrendReq(hl="vi-VN", tz=420)
        trending_searches = pytrends.trending_searches(pn="vietnam").head(50)[0].tolist()
        if not trending_searches:
            raise ValueError("Không lấy được từ khóa từ Google Trends.")
        
        cache = {"date": today, "keywords": trending_searches}
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        print("✅ Đã lấy và lưu từ khóa hot từ Google Trends.")
        return trending_searches
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy Google Trends: {str(e)}")
        print("🔄 Sử dụng danh sách dự phòng.")
        return random.sample(FALLBACK_KEYWORDS, min(50, len(FALLBACK_KEYWORDS)))

def search_bing(driver, keyword):
    print(f"Đang thực hiện tìm kiếm: {keyword}")
    try:
        driver.get("https://www.bing.com")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "sb_form_q"))
        )
        print("Đã truy cập Bing")

        tick_recaptcha_if_present(driver)

        search_box = driver.find_element(By.ID, "sb_form_q")
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        print(f"Đã nhập và tìm kiếm: {keyword}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "b_results"))
        )
        
        return True
    except TimeoutException:
        print("❌ Timeout khi tải trang Bing hoặc kết quả.")
        return False
    except Exception as e:
        print(f"Lỗi trong quá trình tìm kiếm: {str(e)}")
        traceback.print_exc()
        return False

def main():
    global driver
    driver = init_driver()
    if driver is None:
        print("Không thể khởi tạo driver, thoát chương trình.")
        return

    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Kiểm tra và hoàn thành Daily Sets
        if not check_daily_sets(driver):
            print("⚠️ Không thể hoàn thành tất cả Daily Sets. Tiếp tục tìm kiếm vô hạn.")

        # Bắt đầu tìm kiếm vô hạn
        print("🚀 Bắt đầu tìm kiếm vô hạn trên Bing...")
        last_keyword_fetch_date = None
        keywords = []

        while True:
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_keyword_fetch_date != current_date:
                keywords = get_hot_keywords()
                last_keyword_fetch_date = current_date
                print(f"📋 Số từ khóa hot hôm nay: {len(keywords)}")

            if not keywords:
                print("⚠️ Không có từ khóa, sử dụng dự phòng.")
                keywords = random.sample(FALLBACK_KEYWORDS, min(50, len(FALLBACK_KEYWORDS)))

            keyword = random.choice(keywords)
            if not search_bing(driver, keyword):
                print(f"Tìm kiếm {keyword} thất bại, thử lại...")
                time.sleep(5)
                continue
            
            current_hash = get_page_hash(driver)

            
            time.sleep(random.uniform(2, 5))
        
    except Exception as e:
        print(f"Lỗi trong vòng lặp chính: {str(e)}")
        traceback.print_exc()
    finally:
        print("🛑 Kết thúc chương trình.")
        if driver is not None:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()