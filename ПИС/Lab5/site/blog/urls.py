from django.urls import path
from .views import posts_list, post_detail, post_create

urlpatterns = [
    path('', posts_list, name='posts_list'),
    path('post/<int:pk>/', post_detail, name='post_detail'),
    path('post/new/', post_create, name='post_create'),
]
