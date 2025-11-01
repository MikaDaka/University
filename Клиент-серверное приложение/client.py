import os
import sys
import json
import time
import threading
import asyncio
import tkinter as tk
from tkinter import ttk

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

POLL_INTERVAL_DEFAULT = 3

def parse_hostport(s: str, default_port: int):
    if not s:
        return "localhost", default_port
    if ":" in s:
        host, port = s.split(":", 1)
        try:
            return host, int(port)
        except Exception:
            return host, default_port
    return s, default_port

class AsyncClient:
    def __init__(self, s1_addr, s2_addr, ui_callback, poll_interval=POLL_INTERVAL_DEFAULT):
        self.s1_addr = s1_addr
        self.s2_addr = s2_addr
        self.ui_callback = ui_callback
        self.poll_interval = poll_interval
        self.loop = asyncio.new_event_loop()
        self.s1_reader = self.s1_writer = None
        self.s2_reader = self.s2_writer = None
        self._stop = False
        self._tasks = []
        self._registered = False
        self._auto = True
        self._connected_s1 = False
        self._connected_s2 = False

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._stop = True
        def _stop_loop():
            if self._registered:
                asyncio.run_coroutine_threadsafe(self._do_register(False), self.loop)
            for w in (self.s1_writer, self.s2_writer):
                try:
                    if w:
                        w.close()
                except Exception:
                    pass
            for t in list(self._tasks):
                try:
                    t.cancel()
                except Exception:
                    pass
            try:
                self.loop.stop()
            except Exception:
                pass
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(_stop_loop)
        else:
            _stop_loop()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.create_task(self._main())
            self.loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop=self.loop)
            for p in pending:
                p.cancel()
            try:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            try:
                self.loop.close()
            except Exception:
                pass

    async def _connect_retry(self, addr, tag):
        host, port = addr
        while not self._stop:
            try:
                r, w = await asyncio.open_connection(host, port)
                self.ui_callback("log", f"Подключено к {tag} {host}:{port}")
                
                if self._registered:
                    await self._send(w, {"type": "REGISTER"})
                
                if tag == "Server1":
                    self._connected_s1 = True
                else:
                    self._connected_s2 = True
                return r, w
            except Exception as e:
                self.ui_callback("log", f"Ошибка подключения к {tag} {host}:{port}: {e}")
                await asyncio.sleep(2)
        return None, None

    async def _disconnect_server(self, tag):
        if tag == "s1" and self.s1_writer:
            try:
                if self._registered:
                    await self._send(self.s1_writer, {"type": "UNREGISTER"})
                self.s1_writer.close()
                await self.s1_writer.wait_closed()
            except Exception:
                pass
            self.s1_reader = self.s1_writer = None
            self._connected_s1 = False
            self.ui_callback("log", f"Отключено от Server1")
        elif tag == "s2" and self.s2_writer:
            try:
                if self._registered:
                    await self._send(self.s2_writer, {"type": "UNREGISTER"})
                self.s2_writer.close()
                await self.s2_writer.wait_closed()
            except Exception:
                pass
            self.s2_reader = self.s2_writer = None
            self._connected_s2 = False
            self.ui_callback("log", f"Отключено от Server2")

    async def _main(self):
        if self._connected_s1:
            self.s1_reader, self.s1_writer = await self._connect_retry(self.s1_addr, "Server1")
        if self._connected_s2:
            self.s2_reader, self.s2_writer = await self._connect_retry(self.s2_addr, "Server2")

        if self.s1_reader:
            self._tasks.append(self.loop.create_task(self._listener(self.s1_reader, "s1")))
        if self.s2_reader:
            self._tasks.append(self.loop.create_task(self._listener(self.s2_reader, "s2")))
        
        self._tasks.append(self.loop.create_task(self._poller()))

    async def _send(self, writer, obj):
        try:
            if writer and not writer.is_closing():
                writer.write((json.dumps(obj) + "\n").encode("utf-8"))
                await writer.drain()
                return True
        except Exception as e:
            self.ui_callback("log", f"Ошибка отправки: {e}")
        return False

    async def _poller(self):
        while not self._stop:
            if self._auto and not self._registered:
                await self._send_poll()
            await asyncio.sleep(self.poll_interval)

    async def _send_poll(self):
        if self.s1_writer and self._connected_s1:
            await self._send(self.s1_writer, {"type":"POLL"})
        if self.s2_writer and self._connected_s2:
            await self._send(self.s2_writer, {"type":"POLL"})

    async def _listener(self, reader, tag):
        def format_uptime(sec):
            sec = int(sec or 0)
            days, sec = divmod(sec, 86400)
            hours, sec = divmod(sec, 3600)
            minutes, seconds = divmod(sec, 60)
            parts = []
            if days:
                parts.append(f"{days} д")
            if hours:
                parts.append(f"{hours} ч")
            if minutes:
                parts.append(f"{minutes} мин")
            parts.append(f"{seconds} с")
            return " ".join(parts)

        def fmt_bytes_mb(n):
            try:
                n = int(n or 0)
            except Exception:
                n = 0
            mb = n / (1024 * 1024)
            s = f"{mb:,.2f}".replace(",", " ")
            return f"{s} МБ"

        while not self._stop:
            try:
                line = await reader.readline()
                if not line:
                    self.ui_callback("log", f"{tag} отключился")
                    if tag == "s1":
                        self._connected_s1 = False
                    else:
                        self._connected_s2 = False
                    break
                
                try:
                    msg = json.loads(line.decode("utf-8").strip())
                except Exception:
                    continue
                
                if msg.get("type") == "DATA":
                    p = msg.get("payload", {})
                    if tag == "s1":
                        total = p.get("swap_total", 0)
                        free = p.get("swap_free", 0)
                        total_str = fmt_bytes_mb(total)
                        free_str = fmt_bytes_mb(free)
                        txt = f"Память подкачки — всего: {total_str}  свободно: {free_str}"
                        self.ui_callback("s1", txt)
                    elif tag == "s2":
                        uptime = p.get("uptime_seconds", 0)
                        w = p.get("screen_width", 0)
                        h = p.get("screen_height", 0)
                        try:
                            uptime = int(uptime or 0)
                            w = int(w or 0)
                            h = int(h or 0)
                        except Exception:
                            uptime, w, h = 0, 0, 0
                        uptime_str = format_uptime(uptime)
                        screen_str = f"{w}×{h} px" if w and h else "размер экрана неизвестен"
                        txt = f"Время работы: {uptime_str}   Экран: {screen_str}"
                        self.ui_callback("s2", txt)
                
                elif msg.get("type") == "ACK":
                    message = msg.get('message', '')
                    self.ui_callback("log", f"{message}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.ui_callback("log", f"Listener {tag} ошибка: {e}")
                if tag == "s1":
                    self._connected_s1 = False
                else:
                    self._connected_s2 = False
                break

        if not self._stop:
            self.ui_callback("log", f"Попытка переподключения к {tag}")
            if tag == "s1" and self._connected_s1:
                self.s1_reader, self.s1_writer = await self._connect_retry(self.s1_addr, "Server1")
                if self.s1_reader:
                    self._tasks.append(self.loop.create_task(self._listener(self.s1_reader, "s1")))
            elif tag == "s2" and self._connected_s2:
                self.s2_reader, self.s2_writer = await self._connect_retry(self.s2_addr, "Server2")
                if self.s2_reader:
                    self._tasks.append(self.loop.create_task(self._listener(self.s2_reader, "s2")))

    def connect_server(self, which):
        if which == "s1" and not self._connected_s1:
            self._connected_s1 = True
            asyncio.run_coroutine_threadsafe(self._reconnect_server("s1"), self.loop)
            self.ui_callback("log", "Подключаем Server1...")
        elif which == "s2" and not self._connected_s2:
            self._connected_s2 = True
            asyncio.run_coroutine_threadsafe(self._reconnect_server("s2"), self.loop)
            self.ui_callback("log", "Подключаем Server2...")

    def disconnect_server(self, which):
        if which == "s1" and self._connected_s1:
            self._connected_s1 = False
            asyncio.run_coroutine_threadsafe(self._disconnect_server("s1"), self.loop)
        elif which == "s2" and self._connected_s2:
            self._connected_s2 = False
            asyncio.run_coroutine_threadsafe(self._disconnect_server("s2"), self.loop)

    async def _reconnect_server(self, tag):
        if tag == "s1":
            self.s1_reader, self.s1_writer = await self._connect_retry(self.s1_addr, "Server1")
            if self.s1_reader:
                self._tasks.append(self.loop.create_task(self._listener(self.s1_reader, "s1")))
        else:
            self.s2_reader, self.s2_writer = await self._connect_retry(self.s2_addr, "Server2")
            if self.s2_reader:
                self._tasks.append(self.loop.create_task(self._listener(self.s2_reader, "s2")))

    def toggle_register(self):
        if not self._connected_s1 or not self._connected_s2:
            self.ui_callback("log", "Нельзя подписаться: не все серверы подключены")
            return self._registered
        
        new_state = not self._registered
        self._registered = new_state
        
        asyncio.run_coroutine_threadsafe(self._do_register(new_state), self.loop)
        
        self.ui_callback("log", f"{'Подписываемся' if new_state else 'Отписываемся'} на push-уведомления...")
        return new_state

    async def _do_register(self, register: bool):
        command = "REGISTER" if register else "UNREGISTER"
        success_count = 0
        
        if self.s1_writer and self._connected_s1:
            if await self._send(self.s1_writer, {"type": command}):
                success_count += 1
        
        if self.s2_writer and self._connected_s2:
            if await self._send(self.s2_writer, {"type": command}):
                success_count += 1
        
        if success_count > 0:
            self.ui_callback("log", f"{'Подписка оформлена' if register else 'Подписка отменена'} на {success_count} серверов")
        else:
            self.ui_callback("log", f"Не удалось {'подписаться' if register else 'отписаться'}")

    def set_auto(self, flag: bool):
        self._auto = bool(flag)

    def set_interval(self, sec: int):
        try:
            self.poll_interval = max(1, int(sec))
        except Exception:
            self.poll_interval = POLL_INTERVAL_DEFAULT

    def update_addresses(self, s1_addr, s2_addr):
        self.s1_addr = s1_addr
        self.s2_addr = s2_addr

class ClientUI:
    def __init__(self, root):
        self.root = root
        root.title("Клиент мониторинга системы (Linux)")
        
        # Установка размера шрифта для лучшей читаемости в Linux
        self.style = ttk.Style()
        self.style.configure('.', font=('DejaVu Sans', 10))
        
        self.frame = ttk.Frame(root, padding=10)
        self.frame.grid()

        # Настройки подключения
        ttk.Label(self.frame, text="Адрес Server1 (host:port)").grid(column=0, row=0, sticky="w")
        self.s1_entry = ttk.Entry(self.frame, width=25)
        self.s1_entry.insert(0, "localhost:8081")
        self.s1_entry.grid(column=1, row=0, sticky="w")

        ttk.Label(self.frame, text="Адрес Server2 (host:port)").grid(column=0, row=1, sticky="w")
        self.s2_entry = ttk.Entry(self.frame, width=25)
        self.s2_entry.insert(0, "localhost:8082")
        self.s2_entry.grid(column=1, row=1, sticky="w")

        ttk.Label(self.frame, text="Интервал автоопроса (с)").grid(column=0, row=2, sticky="w")
        self.interval_spin = ttk.Spinbox(self.frame, from_=1, to=60, width=5)
        self.interval_spin.set(str(POLL_INTERVAL_DEFAULT))
        self.interval_spin.grid(column=1, row=2, sticky="w")

        self.btn_apply = ttk.Button(self.frame, text="Применить настройки", command=self.apply_settings)
        self.btn_apply.grid(column=2, row=2, sticky="w", padx=(10,0))

        ttk.Separator(self.frame, orient="horizontal").grid(column=0, row=3, columnspan=4, sticky="ew", pady=10)

        # Server 1 блок - ТОЛЬКО подключение/отключение
        ttk.Label(self.frame, text="Server1 (файл подкачки)").grid(column=0, row=4, sticky="w")
        self.s1_var = tk.StringVar(value="--- не подключено ---")
        ttk.Label(self.frame, textvariable=self.s1_var, wraplength=400).grid(column=1, row=4, sticky="w", columnspan=2)
        
        self.btn_connect_s1 = ttk.Button(self.frame, text="Подключить", command=lambda: self.client.connect_server("s1"))
        self.btn_connect_s1.grid(column=3, row=4, sticky="w")
        
        self.btn_disconnect_s1 = ttk.Button(self.frame, text="Отключить", command=lambda: self.client.disconnect_server("s1"))
        self.btn_disconnect_s1.grid(column=4, row=4, sticky="w")

        # Server 2 блок - ТОЛЬКО подключение/отключение
        ttk.Label(self.frame, text="Server2 (время работы и экран)").grid(column=0, row=5, sticky="w")
        self.s2_var = tk.StringVar(value="--- не подключено ---")
        ttk.Label(self.frame, textvariable=self.s2_var, wraplength=400).grid(column=1, row=5, sticky="w", columnspan=2)
        
        self.btn_connect_s2 = ttk.Button(self.frame, text="Подключить", command=lambda: self.client.connect_server("s2"))
        self.btn_connect_s2.grid(column=3, row=5, sticky="w")
        
        self.btn_disconnect_s2 = ttk.Button(self.frame, text="Отключить", command=lambda: self.client.disconnect_server("s2"))
        self.btn_disconnect_s2.grid(column=4, row=5, sticky="w")

        # Лог
        ttk.Label(self.frame, text="Лог событий:").grid(column=0, row=6, sticky="w", pady=(5,0))
        self.log_box = tk.Text(self.frame, width=80, height=12, font=('DejaVu Sans Mono', 9))
        self.log_box.grid(column=0, row=7, columnspan=5, pady=5)

        # Управление
        frame_controls = ttk.Frame(self.frame)
        frame_controls.grid(column=0, row=8, columnspan=5, sticky="ew", pady=5)
        
        self.btn_reg = ttk.Button(frame_controls, text="Подписаться на пуш", command=self.on_toggle_register)
        self.btn_reg.pack(side="left", padx=(0, 10))

        self.auto_var = tk.BooleanVar(value=True)
        self.chk_auto = ttk.Checkbutton(frame_controls, text="Автоопрос включён", variable=self.auto_var, command=self.on_toggle_auto)
        self.chk_auto.pack(side="left", padx=(0, 10))

        self.btn_quit = ttk.Button(frame_controls, text="Выход", command=self.on_close)
        self.btn_quit.pack(side="right")

        # Инициализация клиента
        s1 = parse_hostport(self.s1_entry.get(), 8081)
        s2 = parse_hostport(self.s2_entry.get(), 8082)
        interval = int(self.interval_spin.get())
        
        self.client = AsyncClient(s1, s2, self.ui_callback, poll_interval=interval)
        self.client.start()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def apply_settings(self):
        s1 = parse_hostport(self.s1_entry.get(), 8081)
        s2 = parse_hostport(self.s2_entry.get(), 8082)
        try:
            interval = int(self.interval_spin.get())
        except Exception:
            interval = POLL_INTERVAL_DEFAULT

        self.client.set_interval(interval)
        self.client.update_addresses(s1, s2)
        self.ui_callback("log", f"Применены новые настройки")

    def ui_callback(self, kind, message):
        if kind == "s1":
            self.root.after(0, self.s1_var.set, message)
        elif kind == "s2":
            self.root.after(0, self.s2_var.set, message)
        elif kind == "log":
            self.root.after(0, self._append_log, message)

    def _append_log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")

    def on_toggle_register(self):
        new_state = self.client.toggle_register()
        self.btn_reg.config(text="Отписаться" if new_state else "Подписаться на пуш")

    def on_toggle_auto(self):
        flag = bool(self.auto_var.get())
        self.client.set_auto(flag)
        self.ui_callback("log", "Автоопрос включён" if flag else "Автоопрос отключён")

    def on_close(self):
        try:
            self.client.stop()
        except Exception:
            pass
        self.root.after(200, self.root.destroy)

def main():
    root = tk.Tk()
    app = ClientUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()