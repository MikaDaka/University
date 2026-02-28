from django.shortcuts import render
from .models import Post

def posts_list(request):
    posts = Post.objects.all().order_by('-created_date')
    return render(request, 'blog/posts_list.html', {'posts': posts})
