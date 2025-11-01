# Общие вспомогательные функции для серверов — отправка логов на централизованный LogServer.
# Пояснение: используем простое TCP-соединение для посылки одной JSON-строки.
import os
import sys
import json
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

# адрес логсервера по умолчанию (localhost). 
LOGGING_SERVER = ("127.0.0.1", 8888)

def send_log(sender, level, message):
    try:
        data = {"sender": sender, "level": level, "message": str(message), "ts": time.time()}
        url = f"http://{LOGGING_SERVER[0]}:{LOGGING_SERVER[1]}/log"
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        # логирование ошибок логирования не критично — игнорируем
        pass

