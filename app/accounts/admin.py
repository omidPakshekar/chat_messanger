from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from django import forms
from django.core.exceptions import ValidationError


from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username']

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm

    list_display = ('id', 'username', 'date_joined', 'last_login', 'is_admin', 'is_staff')
    search_fields = ('id', 'username')
    readonly_fields = ('id', 'date_joined',  'last_login')
    
    filter_horizontal = ()
    list_display = ()
    fieldsets = ()


admin.site.register(CustomUser)
