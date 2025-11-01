import os
import sys
import asyncio
import json
import time
import platform
import psutil
from server_base import send_log

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

HOST = "0.0.0.0"
PORT = 8081
SERVER_NAME = "server1"

def get_swap_info():
    try:
        swap = psutil.swap_memory()
        return swap.total, swap.free
    except Exception as e:
        print(f"Ошибка получения информации о swap: {e}")
        return 0, 0

class Server1:
    def __init__(self):
        self.clients_last = {}
        self.subscribers = set()
        self.current = None
        self.lock = asyncio.Lock()
        self.client_count = 0

    async def get_data(self):
        total, free = get_swap_info()
        return {"swap_total": total, "swap_free": free, "ts": int(time.time())}

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
                print("Server1: Отправлены данные подписчику")
            except Exception:
                dead.append(w)
        for w in dead:
            self.subscribers.discard(w)

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        client_id = self.client_count + 1
        self.client_count += 1
        
        print(f"Server1: Клиент #{client_id} подключился с {addr}")
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
                if t == "REGISTER":
                    self.subscribers.add(writer)
                    # ОТПРАВЛЯЕМ ДАННЫЕ СРАЗУ ПРИ ПОДПИСКЕ
                    async with self.lock:
                        cur = self.current
                        if cur is not None:
                            writer.write((json.dumps({"type":"DATA","payload":cur}) + "\n").encode("utf-8"))
                            await writer.drain()
                            self.clients_last[writer] = cur
                    
                    writer.write((json.dumps({"type":"ACK","message":"REGISTERED"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    print(f"Server1: Клиент #{client_id} подписался на push-уведомления, данные отправлены")
                    
                elif t == "UNREGISTER":
                    self.subscribers.discard(writer)
                    writer.write((json.dumps({"type":"ACK","message":"UNREGISTERED"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    print(f"Server1: Клиент #{client_id} отписался от push-уведомлений")
                    
                else:
                    writer.write((json.dumps({"type":"ACK","message":"UNKNOWN"}) + "\n").encode("utf-8"))
                    await writer.drain()
                    
        except Exception as e:
            print(f"Server1: Ошибка с клиентом #{client_id}: {e}")
            
        finally:
            print(f"Server1: Клиент #{client_id} отключился")
            send_log(SERVER_NAME, "INFO", f"Client disconnected {addr}")
            self.subscribers.discard(writer)
            self.clients_last.pop(writer, None)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

async def main():
    s = Server1()
    asyncio.create_task(s.start_monitor())
    srv = await asyncio.start_server(s.handle_client, HOST, PORT)
    
    print(f"Server1 запущен на {HOST}:{PORT}")
    print("Ожидание подключений клиентов...")
    send_log(SERVER_NAME, "INFO", f"Started on {HOST}:{PORT}")
    
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())