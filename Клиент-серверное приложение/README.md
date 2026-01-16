# Клиент-серверное приложение мониторинга 

## Что в проекте
- server1.py — Server1 (порт 8081): swap total/free в байтах.
- server2.py — Server2 (порт 8082): uptime и screen WxH.
- logging_server.py — LogServer (порт 8888): сохраняет логи в logs/{sender}.log.
- client.py — GUI клиент (Tkinter), русифицированный.
- server_base.py — helper send_log.
- run_all.bat — скрипт запуска.
- Dockerfile — контейнеризация клиента.

## Запуск
1. Установите Python 3.10+.
2. (Опционально) Установите зависимости: `pip install -r requirements.txt`.
3. Запустите `run_all.bat`.

## Docker (GUI)
- Построить: `docker build -t client-gui -f Dockerfile.client.gui .`
- Запустить (Linux host): `docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --network=host client-gui`

## Примечания
- Серверы реализуют lock‑порт, чтобы предотвратить повторный запуск.
- Серверы отправляют DATA подписчикам только при реальном изменении payload (ts исключён из сравнения).
- LogServer сохраняет JSON‑логи с меткой времени.


