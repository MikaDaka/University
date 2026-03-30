from typing import Self

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        help_text="Используйте уникальное имя. Допустимы буквы, цифры и символы @/./+/-/_"
    )

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        help_text=(
            "Пароль должен содержать минимум 8 символов, "
            "не быть слишком простым и не состоять только из цифр."
        )
    )

    password2 = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput,
        help_text="Введите тот же пароль ещё раз."
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует.")
        return username
    

