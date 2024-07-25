from django import forms
from django.contrib.auth.forms import UserChangeForm

from authorization.models import CustomUser


class EditUserForm(UserChangeForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False  # Сделаем поле необязательным
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        required=False  # Сделаем поле необязательным
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:  # Если есть хоть одно поле не пустое
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:  # Теперь меняем пароль только если оба поля совпадают
            user.set_password(password)
        if commit:
            user.save()
        return user

