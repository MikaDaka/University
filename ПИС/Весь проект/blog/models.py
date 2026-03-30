from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField("Заголовок", max_length=200, unique=True)
    text = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
