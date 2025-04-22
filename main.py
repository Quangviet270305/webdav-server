from wsgidav.server.run_server import run
import os

# Tạo thư mục lưu trữ file nếu chưa có
if not os.path.exists("webdav"):
    os.makedirs("webdav")

# Cấu hình WebDAV
config = {
    "host": "0.0.0.0",
    "port": int(os.environ.get("PORT", 8080)),
    "provider_mapping": {"/": {"root": "./webdav", "readonly": False}},
    "simple_dc": {
        "user_mapping": {"*": {"admin": {"password": "password"}}}
    },
}

if __name__ == "__main__":
    run(config)
