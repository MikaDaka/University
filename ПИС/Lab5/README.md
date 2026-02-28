# Лабораторная работа №5  

Создание формы и представления для нового поста.

## Реализовано

- модель Post
- форма PostForm
- страница создания поста
- обработка POST‑запроса
- перенаправление на список постов
- шаблоны posts_list, post_detail, post_create

## Запуск

```bash
cd mysite
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
