import os
import sys
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

PORT = 8888
LOG_DIR = os.path.join(BASE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/log":
            self.send_response(404)
            self.end_headers()
            return
        
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length)
        
        try:
            data = json.loads(body.decode('utf-8'))
            sender = data.get("sender", "unknown")
            message = data.get("message", "")
            level = data.get("level", "INFO")
            
            # ВЫВОД В КОНСОЛЬ ЛОГСЕРВЕРА
            print(f"LogServer: [{sender}] {level} - {message}")
            
            fname = os.path.join(LOG_DIR, f"{sender}.log")
            with open(fname, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        except Exception as e:
            print(f"LogServer: Ошибка обработки лога: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def log_message(self, format, *args):
        # Подавляем стандартные логи сервера
        return

def run():
    server = HTTPServer(("", PORT), Handler)
    print(f"LogServer запущен на порту {PORT}")
    print(f"Логи сохраняются в: {LOG_DIR}")
    print("Ожидание лог-сообщений...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🔌 LogServer остановлен")
        server.shutdown()

if __name__ == "__main__":
    run()

