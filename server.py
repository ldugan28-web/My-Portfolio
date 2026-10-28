import json
import mimetypes
import os
import queue
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent
MAX_MESSAGES = 50
MAX_BODY_BYTES = 4096


class ChatHub:
    def __init__(self):
        self.messages = deque(maxlen=MAX_MESSAGES)
        self.clients = set()
        self.lock = threading.Lock()

    def subscribe(self, client):
        with self.lock:
            self.clients.add(client)
            messages = list(self.messages)
        return messages

    def unsubscribe(self, client):
        with self.lock:
            self.clients.discard(client)

    def publish(self, name, text):
        message = {
            "id": str(uuid.uuid4()),
            "name": name,
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        with self.lock:
            self.messages.append(message)
            for client in tuple(self.clients):
                try:
                    client.put_nowait({"event": "message", "data": message})
                except queue.Full:
                    while not client.empty():
                        try:
                            client.get_nowait()
                        except queue.Empty:
                            break
                    client.put_nowait({"event": "history", "data": list(self.messages)})
        return message


chat = ChatHub()


class ChatRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/chat/stream":
            self.stream_chat()
        elif path == "/api/chat/health":
            self.send_json(200, {"ok": True})
        else:
            self.serve_file(path)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/chat/send":
            self.send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request"})
            return
        if content_length < 1 or content_length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "Message payload is too large"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Invalid JSON"})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Invalid message"})
            return

        name = payload.get("name")
        text = payload.get("text")
        if not isinstance(name, str) or not isinstance(text, str):
            self.send_json(400, {"error": "Name and message are required"})
            return
        name = name.strip()
        text = text.strip()
        if not name or len(name) > 24 or not text or len(text) > 500:
            self.send_json(400, {"error": "Name must be 1-24 characters and message 1-500 characters"})
            return

        message = chat.publish(name, text)
        self.send_json(201, {"ok": True, "id": message["id"]})

    def stream_chat(self):
        client = queue.Queue(maxsize=64)
        history = chat.subscribe(client)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        try:
            self.wfile.write(b"retry: 3000\n\n")
            self.write_event("history", history)
            while True:
                try:
                    event = client.get(timeout=15)
                    self.write_event(event["event"], event["data"])
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            chat.unsubscribe(client)

    def write_event(self, event_name, data):
        serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        payload = f"event: {event_name}\ndata: {serialized}\n\n".encode("utf-8")
        self.wfile.write(payload)
        self.wfile.flush()

    def serve_file(self, request_path):
        relative_path = unquote(request_path).lstrip("/") or "index.html"
        path_parts = Path(relative_path).parts
        if any(part.startswith(".") for part in path_parts) or relative_path in {"server.py", "CHAT_SETUP.md", "render.yaml"}:
            self.send_error(404)
            return

        file_path = (ROOT / relative_path).resolve()
        if not file_path.is_relative_to(ROOT) or not file_path.is_file():
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        if "/api/chat/stream" not in self.path:
            super().log_message(format_string, *args)


class ChatHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8001"))
    server = ChatHTTPServer(("0.0.0.0", port), ChatRequestHandler)
    print(f"Portfolio and chat available at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping chat server")
        server.server_close()