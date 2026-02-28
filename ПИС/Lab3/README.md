# Лабораторная работа №3  

Создание модели данных и её регистрация в административном интерфейсе Django.

## Что реализовано

- модель Post (title, text, created_date)
- регистрация модели в админке
- вывод всех постов на главной странице
- шаблон posts_list.html

## Команды для запуска

```bash
cd mysite
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
