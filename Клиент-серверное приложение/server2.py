import os
import sys
import asyncio
import json
import time
import tkinter as tk
from server_base import send_log

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

HOST = "0.0.0.0"
PORT = 8082
SERVER_NAME = "server2"

class Server2:
    def __init__(self):
        self.clients_last = {}
        self.subscribers = set()
        self.current = None
        self.lock = asyncio.Lock()
        self.start_time = time.time()
        self.client_count = 0

    async def get_screen_size(self):
        try:
            # Способ 1: через tkinter (основной)
            root = tk.Tk()
            root.withdraw()  # Скрываем окно
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            root.destroy()
            return w, h
        except Exception as e:
            print(f"Server2: Ошибка получения разрешения экрана через tkinter: {e}")
            try:
                # Способ 2: через ctypes (резервный для Windows)
                import ctypes
                user32 = ctypes.windll.user32
                w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                h = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                return w, h
            except Exception:
                # Способ 3: значения по умолчанию
                print("Server2: Используются значения разрешения по умолчанию 1920x1080")
                return 1920, 1080

    async def get_data(self):
        uptime = int(time.time() - self.start_time)
        w, h = await self.get_screen_size()
        return {"uptime_seconds": uptime, "screen_width": w, "screen_height": h, "ts": int(time.time())}

    async def start_monitor(self):
        while True:
            data = await self.get_data()
            data_for_comparison = {k: v for k, v in data.items() if k != "ts"}
            current_for_comparison = {k: v for k, v in (self.current or {}).items() if k != "ts"}
            
            async with self.lock:
                changed = (current_for_comparison != data_for_comparison)
                self.current = data
            
            if changed:
                await self.notify_subscribers(data)
                send_log(SERVER_NAME, "INFO", f"Data changed: {data}")
            
            await asyncio.sleep(1)

    async def notify_subscribers(self, data):
        dead = []
        for w in list(self.subscribers):
            try:
                w.write((json.dumps({"type":"DATA","payload":data}) + "\n").encode("utf-8"))
                await w.drain()
            except Exception:
                dead.append(w)
        for w in dead:
            self.subscribers.discard(w)

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_id = self.client_count + 1
        self.client_count += 1
        
        # ВЫВОД В КОНСОЛЬ СЕРВЕРА
        print(f"Server2: Клиент #{client_id} подключился с {addr}")
        send_log(SERVER_NAME, "INFO", f"Client connected {addr}")
        
        self.clients_last[writer] = None
        
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                
                try:
                    msg = json.loads(line.decode("utf-8").strip())
                except Exception:
                    continue
                
                t = msg.get("type")
                if t == "POLL":
                    async with self.lock:
                        cur = self.current
                        last = self.clients_last.get(writer)
                        if cur is not None and cur != last:
                            writer.write((json.dumps({"type":"DATA","payload":cur}) + "\n").encode("utf-8"))
                            await writer.drain()
                            self.clients_last[writer] = cur
                            
                elif t == "REGISTER":
                    self.subscribers.add(writer)
                    writer.write((json.dumps({"type":"ACK","message":"REGISTERED"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    print(f"Server2: Клиент #{client_id} подписался на push-уведомления")
                    
                elif t == "UNREGISTER":
                    self.subscribers.discard(writer)
                    writer.write((json.dumps({"type":"ACK","message":"UNREGISTERED"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    print(f"Server2: Клиент #{client_id} отписался от push-уведомлений")
                    
                else:
                    writer.write((json.dumps({"type":"ACK","message":"UNKNOWN"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    
        except Exception as e:
            print(f"Server2: Ошибка с клиентом #{client_id}: {e}")
            
        finally:
            # ВЫВОД В КОНСОЛЬ ПРИ ОТКЛЮЧЕНИИ
            print(f"Server2: Клиент #{client_id} отключился")
            send_log(SERVER_NAME, "INFO", f"Client disconnected {addr}")
            self.subscribers.discard(writer)
            self.clients_last.pop(writer, None)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

async def main():
    s = Server2()
    asyncio.create_task(s.start_monitor())
    srv = await asyncio.start_server(s.handle_client, HOST, PORT)
    
    print(f"Server2 запущен на {HOST}:{PORT}")
    print("Ожидание подключений клиентов...")
    send_log(SERVER_NAME, "INFO", f"Started on {HOST}:{PORT}")
    
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())