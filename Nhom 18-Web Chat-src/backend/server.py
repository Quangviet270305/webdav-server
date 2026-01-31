import json
import os
from aiohttp import web
from datetime import datetime
from collections import defaultdict
from db import (
    init_db, save_message, load_messages,
    verify_user, create_user, get_user_role,
    save_private_message, load_private_messages,
    get_all_users
)

# ================= INIT =================
init_db()

clients = {}              # ws -> {username, room, role}
rooms = defaultdict(set)  # room -> set(ws)
private_chats = {}        # username -> ws


# ================= UTILS =================
def get_online_users(room):
    return sorted({
        clients[ws]["username"]
        for ws in rooms[room]
        if ws in clients and clients[ws]
    })


async def broadcast(room, data, exclude=None):
    for ws in list(rooms[room]):
        if ws == exclude:
            continue
        try:
            await ws.send_json(data)
        except:
            rooms[room].discard(ws)
            clients.pop(ws, None)


async def send_userlist(room):
    users = get_online_users(room)
    await broadcast(room, {
        "type": "userlist",
        "users": users,
        "count": len(users)
    })


# ================= WEBSOCKET =================
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients[ws] = None

    try:
        async for msg in ws:
            if msg.type != web.WSMsgType.TEXT:
                continue

            try:
                data = json.loads(msg.data)
            except:
                continue

            msg_type = data.get("type")

            # ===== JOIN =====
            if msg_type == "join":
                username = data.get("username", "").strip()
                room = data.get("room", "general")
                role = get_user_role(username)

                clients[ws] = {"username": username, "room": room, "role": role}
                rooms[room].add(ws)
                private_chats[username] = ws

                await ws.send_json({
                    "type": "login_success",
                    "username": username,
                    "role": role,
                    "room": room,
                    "history": load_messages(room),
                    "all_users": get_all_users()
                })

                await send_userlist(room)

            # ===== REGISTER =====
            elif msg_type == "register":
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()

                if not username or not password:
                    await ws.send_json({"type": "error", "message": "Thiếu thông tin"})
                    continue

                if create_user(username, password):
                    await ws.send_json({"type": "register_ok"})
                else:
                    await ws.send_json({"type": "error", "message": "Username tồn tại"})

            # ===== LOGIN =====
            elif msg_type == "login":
                username = data.get("username")
                password = data.get("password")
                room = data.get("room", "general")

                if verify_user(username, password):
                    role = get_user_role(username)
                    clients[ws] = {"username": username, "room": room, "role": role}
                    rooms[room].add(ws)
                    private_chats[username] = ws

                    await ws.send_json({
                        "type": "login_success",
                        "username": username,
                        "role": role,
                        "room": room,
                        "history": load_messages(room),
                        "all_users": get_all_users()
                    })

                    await send_userlist(room)
                else:
                    await ws.send_json({"type": "login_fail"})

            # ===== PUBLIC MESSAGE =====
            elif msg_type == "message":
                user = clients.get(ws)
                if not user:
                    continue

                msg = data.get("message", "").strip()
                if not msg:
                    continue

                save_message(user["room"], user["username"], msg)

                await broadcast(user["room"], {
                    "type": "message",
                    "sender": user["username"],
                    "message": msg,
                    "time": datetime.now().strftime("%H:%M")
                })

            # ===== PRIVATE MESSAGE =====
            elif msg_type == "private_message":
                sender = clients[ws]["username"]
                receiver = data.get("to")
                message = data.get("message")

                save_private_message(sender, receiver, message)

                payload = {
                    "type": "private_message",
                    "sender": sender,
                    "receiver": receiver,
                    "message": message,
                    "time": datetime.now().strftime("%H:%M")
                }

                if receiver in private_chats:
                    await private_chats[receiver].send_json(payload)

                payload["is_me"] = True
                await ws.send_json(payload)

            # ===== PRIVATE HISTORY =====
            elif msg_type == "get_private_history":
                me = clients[ws]["username"]
                other = data.get("with_user")
                await ws.send_json({
                    "type": "private_history",
                    "history": load_private_messages(me, other)
                })

            # ===== SWITCH ROOM =====
            elif msg_type == "switch_room":
                user = clients.get(ws)
                new_room = data.get("room")

                if user and new_room and new_room != user["room"]:
                    old_room = user["room"]
                    rooms[old_room].discard(ws)
                    await send_userlist(old_room)

                    user["room"] = new_room
                    rooms[new_room].add(ws)

                    await ws.send_json({
                        "type": "history",
                        "room": new_room,
                        "history": load_messages(new_room)
                    })

                    await send_userlist(new_room)

    finally:
        user = clients.pop(ws, None)
        if user:
            rooms[user["room"]].discard(ws)
            private_chats.pop(user["username"], None)
            await send_userlist(user["room"])

    return ws


# ================= HTTP =================
async def index(request):
    return web.FileResponse("./static/index.html")


# ================= APP =================
app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", ws_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    web.run_app(app, host="0.0.0.0", port=port)
