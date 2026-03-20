from django.shortcuts import render


def home(request):
    """
    Renders the main home page.
    """
    auth_error = request.session.pop('auth_error', None)
    return render(request, 'myapp/home.html', {'auth_error': auth_error})