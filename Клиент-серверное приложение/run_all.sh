#!/usr/bin/env bash
set -euo pipefail

# Путь к каталогу проекта 
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv_course"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"
PY_REQUIREMENTS=("tk" "psutil") 

LOG_SERVER_PORT=8888
SERVER1_PORT=8081
SERVER2_PORT=8082

LOG_SERVER_PY="$PROJECT_DIR/logging_server.py"
SERVER1_PY="$PROJECT_DIR/server1.py"
SERVER2_PY="$PROJECT_DIR/server2.py"
CLIENT_PY="$PROJECT_DIR/client.py"

OUT_LOG="$LOG_DIR/out.log"

usage() {
  cat <<EOF
Использование: $0 [start|stop|status|restart|clean]
  start     Создать venv, установить зависимости и запустить процессы
  stop      Остановить все запущенные процессы (по PID)
  status    Показать статус процессов
  restart   Выполнить stop затем start
  clean     Удалить каталоги .venv_course logs pids
EOF
  exit 1
}

ensure_dirs() {
  mkdir -p "$LOG_DIR"
  mkdir -p "$PID_DIR"
}

create_venv_and_install() {
  if [ ! -x "$PYTHON_BIN" ]; then
    echo "Создаю виртуальное окружение в $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    "$PIP_BIN" install --upgrade pip
    "$PIP_BIN" install psutil
  else
    echo "Виртуальное окружение найдено: $VENV_DIR"
  fi
}

start_process() {
  local name="$1"; shift
  local cmd=("$@")
  local pidfile="$PID_DIR/$name.pid"
  local logfile="$LOG_DIR/$name.log"

  if [ -f "$pidfile" ]; then
    local pid; pid=$(cat "$pidfile" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "$name уже запущен (PID $pid)"
      return 0
    else
      echo "Найден старый PID-файл для $name, удаляю"
      rm -f "$pidfile"
    fi
  fi

  echo "Запускаю $name ..."
  # nohup + redirect; & disown для фонового запуска
  nohup "${cmd[@]}" >>"$logfile" 2>&1 &
  local newpid=$!
  echo "$newpid" > "$pidfile"
  disown "$newpid" 2>/dev/null || true
  echo "$name запущен PID $newpid, лог: $logfile"
}

stop_process() {
  local name="$1"
  local pidfile="$PID_DIR/$name.pid"
  if [ ! -f "$pidfile" ]; then
    echo "PID-файл для $name не найден"
    return 0
  fi
  local pid; pid=$(cat "$pidfile" 2>/dev/null || echo "")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "Останавливаю $name (PID $pid) ..."
    kill "$pid"
    # ждём завершения
    for i in {1..10}; do
      if kill -0 "$pid" 2>/dev/null; then
        sleep 0.5
      else
        break
      fi
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name не завершился, отправляю SIGKILL"
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    echo "Процесс $name не найден по PID $pid"
  fi
  rm -f "$pidfile"
}

status_process() {
  local name="$1"
  local pidfile="$PID_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    local pid; pid=$(cat "$pidfile" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "$name: RUNNING (PID $pid)"
    else
      echo "$name: PID-файл есть, но процесс не найден"
    fi
  else
    echo "$name: STOPPED"
  fi
}

start_all() {
  ensure_dirs
  create_venv_and_install

  # Запуск LogServer
  start_process "logserver" "$PYTHON_BIN" "$LOG_SERVER_PY"

  # Небольшая пауза, чтобы логсервер успел подняться
  sleep 0.5

  # Запуск Server1 и Server2
  start_process "server1" "$PYTHON_BIN" "$SERVER1_PY"
  start_process "server2" "$PYTHON_BIN" "$SERVER2_PY"

  # Запуск GUI клиента 
  start_process "client" "$PYTHON_BIN" "$CLIENT_PY"

  echo "Все службы запущены."
  echo "Логи находятся в $LOG_DIR"
}

stop_all() {
  stop_process "client"
  stop_process "server2"
  stop_process "server1"
  stop_process "logserver"
  echo "Все службы остановлены."
}

status_all() {
  status_process "logserver"
  status_process "server1"
  status_process "server2"
  status_process "client"
}

clean_all() {
  echo "Останавливаю процессы перед удалением"
  stop_all
  echo "Удаляю venv, логи и pid-файлы"
  rm -rf "$VENV_DIR" "$LOG_DIR" "$PID_DIR"
  echo "Готово"
}

# main
if [ $# -lt 1 ]; then usage; fi

case "$1" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  status)
    status_all
    ;;
  restart)
    stop_all
    sleep 0.5
    start_all
    ;;
  clean)
    clean_all
    ;;
  *)
    usage
    ;;
esac
