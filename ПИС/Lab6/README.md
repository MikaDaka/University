# Лабораторная работа №6

Авторизация и регистрация пользователей в Django.

## Реализовано

- форма входа
- форма регистрации
- проверка паролей
- вход, выход, редиректы
- шаблоны login.html и register.html

## Запуск

```bash
cd mysite
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
