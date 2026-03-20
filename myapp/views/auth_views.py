from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def login_view(request):
    """
    Handles login form submissions from the auth modal.
    Looks up the user by email, then authenticates with their password.
    On success: logs the user in and redirects home.
    On failure: stores the error in the session so the modal re-opens with it.
    """
    if request.method == 'POST':
        email    = request.POST.get('email')
        password = request.POST.get('password')
        try:
            username = User.objects.get(email=email).username
            user     = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                request.session['auth_error'] = 'Invalid email or password.'
        except User.DoesNotExist:
            request.session['auth_error'] = 'No account found with that email.'
    return redirect('home')

def logout_view(request):
    """
    Logs the current user out and redirects to the home page.
    Only accepts POST requests (via the logout form) for CSRF protection.
    """
    logout(request)
    return redirect('home')