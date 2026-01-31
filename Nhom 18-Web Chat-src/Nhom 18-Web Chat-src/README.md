# 🚀 Python High-Performance Real-time Chat

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-orange?style=for-the-badge&logo=html5)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-Stable-green?style=for-the-badge)

Một hệ thống nhắn tin trực tuyến thời gian thực (Real-time Chat System) được xây dựng từ con số 0 (From Scratch) sử dụng **Python Asyncio** và giao thức **WebSocket**. Dự án tập trung tối ưu hóa độ trễ (Zero-latency), khả năng chịu tải cao và bảo mật dữ liệu người dùng. Trong quá trình test local, hệ thống hoạt động ổn định với hàng chục kết nối đồng thời.

---

## 📑 Mục Lục

1. [Giới thiệu](#-giới-thiệu)
2. [Tính năng nổi bật](#-tính-năng-nổi-bật)
3. [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
4. [Cấu trúc dự án](#-cấu-trúc-dự-án)
5. [Cài đặt & Vận hành](#-cài-đặt--vận-hành)
6. [Kiến trúc hệ thống (Technical Deep Dive)](#-kiến-trúc-hệ-thống)
7. [Cơ sở dữ liệu (Schema)](#-cơ-sở-dữ-liệu)
8. [Khắc phục sự cố](#-khắc-phục-sự-cố)

---

## 📖 Giới thiệu

Dự án này là giải pháp thay thế cho các ứng dụng chat truyền thống sử dụng HTTP polling (gây chậm trễ). Bằng cách duy trì kết nối hai chiều (Full-duplex) qua WebSocket, tin nhắn được truyền tải tức thì giữa Client và Server.

Hệ thống hỗ trợ đầy đủ quy trình: **Đăng ký -> Đăng nhập -> Chọn phòng -> Chat (Text/Image) -> Lưu trữ lịch sử.**

---

## ✨ Tính năng nổi bật

* **⚡  Low-Latency (Độ trễ rất thấp, gần thời gian thực):** Áp dụng kiến trúc Optimistic UI – Server broadcast tin nhắn ngay khi nhận được, sau đó mới ghi vào cơ sở dữ liệu ở luồng bất đồng bộ, giúp giảm cảm nhận độ trễ của người dùng mà không làm gián đoạn luồng xử lý chính của server.

* **🖼️ Gửi ảnh tốc độ cao:** Hỗ trợ mã hóa Base64 để gửi và hiển thị hình ảnh trực tiếp trong khung chat.
* **👥 Multi-Room (Đa phòng chat):**
    * Phòng Chung (General)
    * Phòng Công Nghệ (Tech)
    * Phòng Game
* **🔐 Bảo mật lớp ứng dụng:**
    * Mật khẩu người dùng được băm (Hashing) bằng thuật toán **SHA-256** (mức bảo mật cơ bản, có thể nâng cấp bằng Salt/Bcrypt trong tương lai).
    * Ngăn chặn SQL Injection cơ bản thông qua Parameterized Queries.
* **💾 Persist Data (Lưu trữ vĩnh viễn):**
    * Tự động lưu tin nhắn vào SQLite.
    * Tự động tải lại 50 tin nhắn gần nhất khi người dùng vào phòng.
* **🎨 Giao diện Responsive:** Hoạt động tốt trên cả Máy tính và trình duyệt Điện thoại.

---

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ | Chi tiết |
| :--- | :--- | :--- |
| **Backend** | Python 3 | Ngôn ngữ xử lý chính. |
| **Network** | `websockets` | Thư viện xử lý giao thức WS/WSS. |
| **Concurrency** | `asyncio` | Xử lý bất đồng bộ (Asynchronous I/O) để chịu tải cao. |
| **Database** | SQLite3 | Hệ quản trị CSDL quan hệ (nhẹ, không cần server riêng). |
| **Security** | `hashlib` | Thư viện mã hóa mật khẩu. |
| **Frontend** | HTML5 / CSS3 | Giao diện người dùng. |
| **Scripting** | Vanilla JS | JavaScript thuần, sử dụng WebSocket API của trình duyệt. |

---

## 📂 Cấu trúc dự án

Để đảm bảo hệ thống vận hành chính xác, cấu trúc thư mục được tổ chức như sau:

```text
ChatApp/
│
├── ⚙️ BACKEND
│   ├── server.py        # [Main] Server WebSocket, xử lý logic luồng tin nhắn.
│   ├── db.py            # [Model] Module giao tiếp với Database (CRUD User/Message).
│   └── chat.db          # [Data] File CSDL (Tự động sinh ra khi chạy server).
│
├── 🌐 FRONTEND
│   ├── index.html       # Trang chủ (Landing Page).
│   ├── register.html    # Trang đăng ký tài khoản.
│   ├── login.html       # Trang đăng nhập.
│   └── chat.html        # Giao diện chat chính (Logic JS client nằm ở đây).
│
└── 📄 README.md        # Tài liệu hướng dẫn chi tiết.

🚀 Cài đặt & Vận hành
1. Yêu cầu tiên quyết
Máy tính đã cài đặt Python 3.7 trở lên.

Đã cài đặt trình quản lý gói pip.

2. Cài đặt thư viện
Mở Terminal (CMD/PowerShell/Terminal) tại thư mục dự án và chạy:
pip install websockets

3. Khởi chạy Server
Chạy lệnh sau để bật máy chủ:
python server.py    
Dấu hiệu thành công: Terminal hiện dòng chữ: 🚀 SERVER ĐANG CHẠY TẠI: ws://localhost:8765

4. Sử dụng
- Truy cập file index.html bằng trình duyệt (Chrome/Edge/Firefox).
- Bấm nút Đăng ký để tạo tài khoản.
- Đăng nhập và bắt đầu chat.
- Để test: Mở thêm 1 tab ẩn danh (Incognito) hoặc trình duyệt khác, đăng nhập nick khác và chat qua lại.

🧠 Kiến trúc hệ thống
Luồng xử lý tin nhắn (The "Non-blocking" Flow)
Hệ thống được thiết kế để không bao giờ để người dùng phải chờ đợi (Blocking):

Client A gửi tin nhắn JSON {"type": "message", "content": "Hello"}.

Server nhận gói tin.

Bước 1 (Ưu tiên): Server ngay lập tức Broadcast (phát tán) tin nhắn tới tất cả các Client B, C, D đang kết nối trong phòng. -> Người dùng thấy tin nhắn ngay lập tức.
Bước 2 (Hậu xử lý): Server mở một luồng riêng (asyncio.to_thread) để thực hiện việc ghi tin nhắn vào file chat.db (thao tác I/O chậm chạp).
Kết quả: Server vẫn rảnh tay để nhận tin nhắn tiếp theo trong khi ổ cứng đang ghi dữ liệu.

🗄 Cơ sở dữ liệu (Schema)

Hệ thống sử dụng SQLite (chat.db) với 3 bảng chính:

1️⃣ Bảng users (Lưu tài khoản người dùng)

| Cột | Kiểu dữ liệu | Mô tả |

| id | INTEGER (PK) | ID tự tăng |
| username | TEXT   | Tên đăng nhập (Duy nhất) |
| password | TEXT   | Mật khẩu đã mã hóa (SHA-256) |
| role     | TEXT   | Quyền người dùng (mặc định: user) |
| created_at | DATETIME | Thời điểm tạo tài khoản |

---

2️⃣ Bảng messages (Lưu lịch sử chat phòng chung)

| Cột | Kiểu dữ liệu | Mô tả |

| id  | INTEGER (PK) | ID tự tăng |
| room |    TEXT     | ID phòng chat (general, tech, game) |
| sender |  TEXT     | Tên người gửi |
| message | TEXT     | Nội dung tin nhắn |
| msg_type | TEXT    | Loại tin nhắn (text / image) |
| created_at | DATETIME | Thời gian gửi |

---

3️⃣ Bảng private_messages (Lưu lịch sử chat riêng)

| Cột | Kiểu dữ liệu | Mô tả |

| id  | INTEGER (PK) | ID tự tăng |
| sender   | TEXT | Người gửi |
| receiver | TEXT | Người nhận |
| message  | TEXT | Nội dung tin nhắn |
| created_at | DATETIME | Thời gian gửi |


🔧 Khắc phục sự cố
1. Lỗi: "Connection Refused" hoặc không kết nối được
Nguyên nhân: Bạn chưa chạy file server.py hoặc đã tắt cửa sổ Terminal.
Cách sửa: Mở lại Terminal và chạy python server.py. Giữ cửa sổ đó luôn mở.

2. Chat trong mạng LAN (Wifi) không được?
Mặc định code đang để ws://localhost:8765. localhost chỉ chạy trên máy của bạn.

Cách sửa:
- Mở CMD, gõ ipconfig (Windows) hoặc ifconfig (Mac/Linux) để lấy địa chỉ IPv4 (Ví dụ: 192.168.1.15).
- Vào các file .html, sửa dòng kết nối thành: const ws = new WebSocket("ws://192.168.1.15:8765");
- Gửi file HTML cho các máy khác trong cùng mạng Wifi.

3. Gửi ảnh bị lag/đơ?
WebSocket gửi dữ liệu dạng Text. Ảnh lớn (>2MB) khi chuyển sang Base64 sẽ thành chuỗi text rất dài (~3 triệu ký tự), gây nghẽn mạng tạm thời.
Khuyến nghị: Chỉ nên gửi ảnh dưới 2MB hoặc ảnh chụp màn hình.

👨‍💻 Tác giả
Dự án được phát triển bởi Nhóm 13 Lập Trình Mạng