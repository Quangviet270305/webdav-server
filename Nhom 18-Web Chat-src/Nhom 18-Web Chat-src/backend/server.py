import asyncio
import websockets
import json
import hashlib
import os
from datetime import datetime
from collections import defaultdict
from db import (
    init_db, save_message, load_messages, 
    verify_user, create_user, get_user_role,
    save_private_message, load_private_messages,
    get_all_users
)

# Khởi tạo DB
init_db()

# Biến toàn cục quản lý kết nối
clients = {}              # ws -> {username, room, role}
rooms = defaultdict(set)  # room -> set(ws)
private_chats = {}        # username -> ws

def online_in_room(room):
    """Số user online trong room"""
    return len(rooms[room])

def get_online_users(room):
    """Lấy danh sách user online trong room"""
    users = []
    for ws in rooms[room]:
        if ws in clients and clients[ws]:
            users.append(clients[ws]["username"])
    # Sắp xếp và loại bỏ trùng lặp
    return sorted(list(set(users)))

async def broadcast(room, data, exclude_ws=None):
    """Gửi tin nhắn đến tất cả trong room"""
    if room not in rooms: return
    
    dead = []
    for ws in rooms[room]:
        if ws == exclude_ws:
            continue
        try:
            await ws.send(json.dumps(data))
        except:
            dead.append(ws)
    
    # Xóa các connection bị hỏng
    for ws in dead:
        rooms[room].discard(ws)
        if ws in clients:
            del clients[ws]

async def send_userlist(room):
    """Gửi danh sách user online cho room đó"""
    users = get_online_users(room)
    await broadcast(room, {
        "type": "userlist",
        "users": users,
        "count": len(users)
    })

async def handler(ws):
    """Xử lý kết nối WebSocket"""
    clients[ws] = None
    
    try:
        async for raw in ws:
            try:
                data = json.loads(raw)
            except:
                continue
            
            msg_type = data.get("type")

            # ========= 1. JOIN (Kết nối lại / F5) =========
            if msg_type == "join":
                username = data.get("username", "").strip()
                room = data.get("room", "general")
                
                role = get_user_role(username)
                
                clients[ws] = {
                    "username": username, 
                    "room": room, 
                    "role": role
                }
                rooms[room].add(ws)
                private_chats[username] = ws
                
                print(f"✅ {username} joined {room}")
                
                # Gửi trạng thái ban đầu + LỊCH SỬ CHAT
                await ws.send(json.dumps({
                    "type": "login_success",
                    "username": username,
                    "role": role,
                    "room": room,
                    "history": load_messages(room), # Gửi lịch sử ngay
                    "all_users": get_all_users()
                }))
                
                await send_userlist(room)

            # ========= 2. REGISTER =========
            elif msg_type == "register":
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()
                
                if not username or not password:
                    await ws.send(json.dumps({"type": "error", "message": "Thiếu thông tin"}))
                    continue
                
                if len(username) < 3:
                    await ws.send(json.dumps({"type": "error", "message": "Username quá ngắn"}))
                    continue
                
                try:
                    if create_user(username, password):
                        await ws.send(json.dumps({"type": "register_ok", "message": "Đăng ký thành công!"}))
                    else:
                        await ws.send(json.dumps({"type": "error", "message": "Username đã tồn tại"}))
                except Exception as e:
                    await ws.send(json.dumps({"type": "error", "message": "Lỗi server"}))

            # ========= 3. LOGIN =========
            elif msg_type == "login":
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()
                room = data.get("room", "general")
                
                if verify_user(username, password):
                    role = get_user_role(username)
                    clients[ws] = {"username": username, "room": room, "role": role}
                    rooms[room].add(ws)
                    private_chats[username] = ws
                    
                    await ws.send(json.dumps({
                        "type": "login_success",
                        "username": username,
                        "role": role,
                        "room": room,
                        "history": load_messages(room), # Gửi lịch sử
                        "all_users": get_all_users()
                    }))
                    
                    await broadcast(room, {
                        "type": "system",
                        "message": f"🎉 {username} đã tham gia"
                    }, exclude_ws=ws)
                    
                    await send_userlist(room)
                else:
                    await ws.send(json.dumps({"type": "login_fail", "message": "Sai mật khẩu"}))

            # ========= 4. MESSAGE (CHAT CÔNG KHAI) =========
            elif msg_type == "message":
                if not clients.get(ws): continue
                user = clients[ws]
                room = user["room"]
                sender = user["username"]
                message = data.get("message", "").strip()
                
                if message:
                    save_message(room, sender, message)
                    await broadcast(room, {
                        "type": "message",
                        "sender": sender,
                        "message": message,
                        "room": room,
                        "time": datetime.now().strftime("%H:%M")
                    })

            # ========= 5. PRIVATE MESSAGE (CHAT RIÊNG) =========
            elif msg_type == "private_message":
                sender = clients[ws]["username"]
                receiver = data.get("to")
                message = data.get("message")
                
                if receiver:
                    save_private_message(sender, receiver, message)
                    
                    payload = {
                        "type": "private_message",
                        "sender": sender,
                        "receiver": receiver,
                        "message": message,
                        "time": datetime.now().strftime("%H:%M")
                    }
                    
                    # Gửi cho người nhận nếu online
                    if receiver in private_chats:
                        target_ws = private_chats[receiver]
                        try:
                            await target_ws.send(json.dumps(payload))
                        except:
                            del private_chats[receiver]

                    # Gửi lại cho người gửi (để hiện lên UI của mình)
                    payload["is_me"] = True
                    await ws.send(json.dumps(payload))

            # ========= 6. GET PRIVATE HISTORY =========
            elif msg_type == "get_private_history":
                me = clients[ws]["username"]
                other = data.get("with_user")
                await ws.send(json.dumps({
                    "type": "private_history",
                    "history": load_private_messages(me, other),
                    "with_user": other
                }))

            # ========= 7. SWITCH ROOM (FIX LỖI MẤT TIN NHẮN TẠI ĐÂY) =========
            elif msg_type == "switch_room":
                new_room = data.get("room")
                user = clients.get(ws)
                
                if user and new_room and new_room != user["room"]:
                    old_room = user["room"]
                    
                    # 1. Rời phòng cũ
                    if ws in rooms[old_room]:
                        rooms[old_room].discard(ws)
                    # Cập nhật list user cho phòng cũ ngay lập tức
                    await send_userlist(old_room)
                    
                    # 2. Vào phòng mới
                    user["room"] = new_room
                    rooms[new_room].add(ws)
                    
                    # 3. Gửi lịch sử phòng mới (QUAN TRỌNG: Key phải là 'history')
                    history_data = load_messages(new_room)
                    await ws.send(json.dumps({
                        "type": "history",       # Client bắt type này
                        "history": history_data, # Client bắt key này để render
                        "room": new_room
                    }))
                    
                    # 4. Cập nhật list user cho phòng mới
                    await send_userlist(new_room)

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Handler error: {e}")
    finally:
        # Dọn dẹp khi ngắt kết nối
        if ws in clients:
            user = clients[ws]
            username = user["username"]
            room = user["room"]
            
            if ws in rooms[room]:
                rooms[room].discard(ws)
            if username in private_chats:
                del private_chats[username]
            
            del clients[ws]
            await send_userlist(room)
            print(f"❌ {username} disconnected")

async def main():
    PORT = int(os.environ.get("PORT", 8765))
    print("=" * 50)
    print("🚀 WebSocket Chat Server đang chạy...")
    print(f"📡 Địa chỉ: ws://0.0.0.0:{PORT}")
    print("=" * 50)

    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())