# 🚦 Tổng Quan Dự Án: Smart Traffic Monitoring System v2

## 📝 Giới Thiệu (Project Overview)
Hệ thống giám sát giao thông thông minh v2 là một nền tảng toàn diện kết hợp phân tích lưu lượng, đếm phương tiện cơ giới thời gian thực dựa trên các luồng video, tích hợp chặt chẽ cùng một trợ lý ảo (AI Chatbot) giúp người dùng và quản trị viên truy vấn tình trạng giao thông bằng câu lệnh tự nhiên.

## 🏗 Kiến Trúc Hệ Thống (System Architecture)
Dự án được xây dựng trên mô hình Client-Server hiện đại, phân tách rõ ràng theo chuẩn Domain-Driven Design:
- **Frontend (Giao diện người dùng)**: Được thiết kế bằng HTML/CSS/Vanilla JS thuần, cấu trúc component hóa (Navbar, Modals, Auth, Charts) để nhẹ, nhanh và dễ dàng tích hợp.
- **Backend (API Server)**: Sử dụng FastAPI, cung cấp cả REST API và WebSocket, đóng vai trò điều hướng, xác thực, và cung cấp dữ liệu real-time.
- **Video Workers (AI Detection & Tracking)**: Xử lý video chạy dưới dạng Multiprocessing nhằm đọc và phân tích video giao thông liên tục bằng phương pháp Deep Learning (YOLO + ByteTrack) mà không làm nghẽn (block) API Server.
- **AI Agent (Chatbot)**: Tích hợp LangGraph & LLM (như Gemini) chạy luồng ReAct Agent, cung cấp cho LLM khả năng "nhìn" và gọi tool lấy dữ liệu real-time của hệ thống để trả lời các truy vấn liên quan đến giao thông.
- **Database (Cơ sở dữ liệu)**: PostgreSQL lưu trữ thông tin Accounts, Phân quyền (Roles), và Lịch sử Chat.

---

## 📁 Cấu Trúc Thư Mục Hệ Thống (Directory Structure)
```text
project_smart_trafic_system/
├── backend/                  # REST API & Video Processing Workers
│   ├── app/
│   │   ├── api/              # Định tuyến REST APIs & WebSockets (auth, traffic, chat, admin)
│   │   ├── core/             # Cấu hình Pydantic, kết nối DB Async, JWT security
│   │   ├── models/           # Các Data Models của SQLAlchemy (User, ChatHistory)
│   │   ├── schemas/          # Pydantic schemas validation request/response
│   │   ├── repositories/     # Các hàm tương tác Database (CRUD)
│   │   ├── services/         # Layer Business Logic
│   │   ├── workers/          # Xử lý luồng Multiprocessing cho tác vụ video stream
│   │   ├── ai/               # Custom Logic AI (Yolov8, Object Tracking) & Chatbot Agents
│   │   └── utils/            # Các tiện ích bổ trợ chung
│   ├── migrations/           # Quản lý Database Migration với Alembic
│   ├── .env.example          # Biến môi trường mẫu cho backend
│   └── requirements.txt      # Thư viện phụ thuộc Python
├── frontend/                 # Web Interface (Kiến trúc Native)
│   ├── assets/               # CSS toàn cục tĩnh, Hình ảnh và Fonts
│   ├── components/           # Các web components dùng chung (UI elements)
│   ├── auth/                 # Trang & Script Logic xác thực, đăng nhập lại qua Google
│   ├── dashboard/            # Giao diện chính hiển thị video/camera giám sát
│   ├── chat/                 # Giao diện AI Chatbot thao tác thời gian thực
│   ├── map/                  # Bản đồ giao thông (Map Components)
│   └── index.html            # Landing / Trích xuất giao diện
├── docker-compose.yml        # Định nghĩa Postgres Database & Các services hỗ trợ Deploy
└── build_guide.md.resolved   # Tài liệu gốc chi tiết các bước setup ban đầu
```

---

## 🛠 Công Nghệ Sử Dụng (Tech Stack)
### 1. Phía Server (Backend)
- **Framework**: Python 3.10+, FastAPI (hỗ trợ async mạnh mẽ).
- **Cơ sở dữ liệu**: PostgreSQL chạy via Docker.
- **ORM & Quản lý Schema**: SQLAlchemy (Async), Alembic (Migrations), Pydantic.
- **Xác thực (Auth)**: Authlib (Google OAuth2), mã hóa JWT (JSON Web Tokens), bcrypt.
- **Real-time**: WebSockets (truyền tải hình ảnh frame và metrics tốc độ 50fps/30fps).

### 2. Phía AI (AI/Computer Vision/LLM)
- **Computer Vision**: Khung phân tích (YOLOv8, OpenVINO Int8) cho phát hiện xe, kết hợp thuật toán ByteTrack theo dõi quỹ đạo phương tiện.
- **Generative AI Analyst**: LangGraph, Google Gemini API kết hợp kịch bản tool-calling linh hoạt.

### 3. Phía Client (Frontend)
- **Giao diện**: HTML5, CSS3 hiện đại, Vanilla Javascript (chia tách module ES6).
- **Tích hợp**: Axios / FetchAPI, Recharts (hoặc Chart.js equivalent) thiết kế Dashboard.

---

## ✨ Các Tính Năng Nổi Bật (Key Features)
1. **Quản trị Xác Thực Hiện Đại (SSO - Single Sign-On):**
   - Đăng nhập 1 chạm qua Google OAuth2 an toàn.
   - Cơ chế lưu trữ Token thông minh (Bearer via localStorage) tối ưu cho việc cross-origin API và WebSockets.

2. **Giám Sát Lưu Lượng Real-Time (Core Analytics):**
   - Stream song song xử lý luồng Frames video tốc độ cao (~30fps) và JSON Metrics gồm lưu lượng đếm xe, mô phỏng mật độ, tốc độ phương tiện.
   - Render giao diện phân tích biểu đồ cực kỳ mượt mà nhờ Websocket.

3. **ReAct Chatbot Agent Tích Hợp Hệ Thống:**
   - Trợ lý khả năng truy vấn dữ liệu gốc của server: *"Đường X hiện tại đang mưa, liệu mật độ xe là bao nhiêu?"* hay *"Vận tốc trung bình của ô tô là bao nhiêu?"*.
   - Khả năng lưu và quản trị lịch sử Chat theo từng End-User account.

4. **Module Quản Trị Hệ Thống (Admin Dashboard):**
   - Theo dõi System Resources của máy chủ (CPU, RAM, usage).
   - Kiểm soát, ủy quyền (Role-based access) cho các user tham gia quản lý.

---

## 🚀 Hướng Dẫn Vận Hành Hệ Thống Nhanh (Quick Start)

**1. Môi trường Background Services (Postgres Database)**
```bash
docker-compose up -d 
```

**2. Khởi tạo Backend Server**
```bash
cd backend
python -m venv venv
# Kích hoạt venv
source venv/bin/activate    # (Linux/Mac)
venv\Scripts\activate       # (Windows)

# Cài đặt thư viện
pip install -r requirements.txt

# Tạo tables dựa trên model thay vì tạo bằng tay
alembic upgrade head

# Chạy server ở Port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Triển Khai Frontend**
Sử dụng một web server đơn giản (Ví dụ Liveserver) phục vụ nội dung HTML tĩnh:
```bash
cd frontend
python -m http.server 5500 (hoặc dùng live server)
# Sau đó tuy cập http://localhost:5500 trên trình duyệt
```

