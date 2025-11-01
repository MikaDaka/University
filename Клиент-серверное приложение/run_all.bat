@echo off
set BASE="C:/Users/MiMi/Desktop/Учёба/МТУСИ_по_курсам/4_курс/Операционные_системы/Курсовая_работа/Клиент-серверное приложение"
cd /d %BASE%
start cmd /k py logging_server.py
start cmd /k py server1.py
start cmd /k py server2.py
start cmd /k py client.py
