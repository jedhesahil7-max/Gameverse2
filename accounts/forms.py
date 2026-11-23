from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Team, Tournament


class UserRegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter username",
            "autocomplete": "username",
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email address",
            "autocomplete": "email",
        })
    )
    password1 = forms.CharField(
        label="Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create a strong password",
            "autocomplete": "new-password",
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")

        if p1:
            try:
                # Validate against configured AUTH_PASSWORD_VALIDATORS
                validate_password(p1)
            except ValidationError as err:
                self.add_error("password1", err)

        return cleaned_data

    def save(self):
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        return User.objects.create_user(username=username, email=email, password=password)


class UserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
            "autocomplete": "username",
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
            "autocomplete": "current-password",
        })
    )


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "game", "description", "logo"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Shadow Strikers",
            }),
            "game": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Valorant, BGMI, CS2, etc.",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe your squad, gameplay style, and goals...",
            }),
            "logo": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Team name cannot be blank.")
        
        # Check uniqueness excluding self if editing
        qs = Team.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A team with this name already exists. Choose a unique squad name!")
        return name
