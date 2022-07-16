from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.views import (PasswordChangeView,
                                       PasswordResetConfirmView,
                                       PasswordResetView)
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordChangeViewCustom(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')


def password_change_done(request):
    template = 'users/password_change_done.html'
    return render(request, template, {})


class PasswordResetViewCustom(PasswordResetView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


def password_reset_done(request):
    template = 'users/password_reset_done.html'
    return render(request, template, {})


class PasswordResetConfirmViewCustom(PasswordResetConfirmView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')


def password_reset_complete(request):
    template = 'users/password_reset_complete.html'
    return render(request, template, {})
