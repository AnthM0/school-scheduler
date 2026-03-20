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


def register_view(request):
    """
    Handles account creation from the auth modal.
    Uses the email address as the username internally.
    On success: creates the user, logs them in, and redirects home.
    On failure: stores the error in the session so the modal re-opens with it.
    """
    if request.method == 'POST':
        name     = request.POST.get('name')
        email    = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            request.session['auth_error'] = 'An account with that email already exists.'
        else:
            user = User.objects.create_user(username=email, email=email, password=password)

            # Split the full name into first and last
            name_parts     = name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name  = name_parts[1] if len(name_parts) > 1 else ''
            user.save()

            login(request, user)
            return redirect('home')

    return redirect('home')


def logout_view(request):
    """
    Logs the current user out and redirects to the home page.
    Only accepts POST requests (via the logout form) for CSRF protection.
    """
    logout(request)
    return redirect('home')