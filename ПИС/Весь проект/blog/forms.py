from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    title = forms.CharField(
        label="Заголовок",
        help_text="Название поста должно быть уникальным."
    )

    body = forms.CharField(
        label="Текст",
        widget=forms.Textarea,
        help_text="Введите содержимое поста."
    )

    class Meta:
        model = Post
        fields = ("title", "body")

    # Проверка уникальности заголовка
    def clean_title(self):
        title = self.cleaned_data["title"]
        if Post.objects.filter(title=title).exists():
            raise forms.ValidationError("Пост с таким заголовком уже существует.")
        return title
