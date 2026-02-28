from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from .forms import PostForm

def posts_list(request):
    posts = Post.objects.all().order_by('-created_date')
    return render(request, 'blog/posts_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('posts_list')
    else:
        form = PostForm()
    return render(request, 'blog/post_create.html', {'form': form})
