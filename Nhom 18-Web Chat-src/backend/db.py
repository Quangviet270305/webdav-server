import sqlite3
import bcrypt
from datetime import datetime

# Kết nối database
conn = sqlite3.connect("chat.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    """Khởi tạo database"""
    # Bảng users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Bảng messages
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT NOT NULL,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        msg_type TEXT DEFAULT 'text',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Bảng private_messages
    cur.execute("""
    CREATE TABLE IF NOT EXISTS private_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tạo admin mặc định nếu chưa có
    if not user_exists("admin"):
        hashed = hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hashed, "admin")
        )
    
    conn.commit()
    print("✅ Database initialized")

def hash_password(password):
    """Hash password với bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Kiểm tra password"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def user_exists(username):
    """Kiểm tra user đã tồn tại chưa"""
    cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
    return cur.fetchone() is not None

def create_user(username, password):
    """Tạo user mới"""
    hashed = hash_password(password)
    cur.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed)
    )
    conn.commit()
    return True

def verify_user(username, password):
    """Xác thực user"""
    cur.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        return verify_password(password, row[0])
    return False

def get_user_role(username):
    """Lấy role của user"""
    cur.execute("SELECT role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    return row[0] if row else "user"

def save_message(room, sender, message, msg_type="text"):
    """Lưu tin nhắn"""
    cur.execute(
        "INSERT INTO messages (room, sender, message, msg_type) VALUES (?, ?, ?, ?)",
        (room, sender, message, msg_type)
    )
    conn.commit()
    return cur.lastrowid

def save_private_message(sender, receiver, message):
    """Lưu tin nhắn riêng"""
    cur.execute(
        "INSERT INTO private_messages (sender, receiver, message) VALUES (?, ?, ?)",
        (sender, receiver, message)
    )
    conn.commit()

def load_messages(room, limit=100):
    """Tải tin nhắn của room"""
    cur.execute(
        """SELECT sender, message, msg_type, 
           strftime('%H:%M', created_at) as time 
           FROM messages 
           WHERE room=? 
           ORDER BY id DESC LIMIT ?""",
        (room, limit)
    )
    rows = cur.fetchall()
    return [
        {
            "sender": r[0], 
            "message": r[1], 
            "type": r[2],
            "time": r[3]
        } 
        for r in reversed(rows)
    ]

def load_private_messages(user1, user2, limit=50):
    """Tải tin nhắn riêng giữa 2 user"""
    cur.execute(
        """SELECT sender, receiver, message, 
           strftime('%H:%M', created_at) as time 
           FROM private_messages 
           WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
           ORDER BY id DESC LIMIT ?""",
        (user1, user2, user2, user1, limit)
    )
    rows = cur.fetchall()
    return [
        {
            "sender": r[0],
            "receiver": r[1],
            "message": r[2],
            "time": r[3]
        }
        for r in reversed(rows)
    ]

def get_all_users():
    """Lấy danh sách tất cả users"""
    cur.execute("SELECT username, role FROM users ORDER BY username")
    return cur.fetchall()

def delete_message(msg_id):
    """Xóa tin nhắn (cho admin)"""
    cur.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()
    return cur.rowcount > 0

# Khởi tạo database khi import
init_db()