from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import datetime, timedelta
from .models import Class, Group

def home(request):
    return render(request, 'myapp/home.html')

def schedule_template(request):
    # Build time slots
    slots = []
    start = datetime.strptime('7:30 AM', '%I:%M %p')
    end = datetime.strptime('4:30 PM', '%I:%M %p')
    current = start
    while current <= end:
        slots.append({
            'label': current.strftime('%I:%M %p').lstrip('0'),
            'value': current.strftime('%H:%M'),
            'is_half': current.minute == 30,
        })
        current += timedelta(minutes=30)

    # Handle new group form submission
    if request.method == 'POST' and 'create_group' in request.POST:
        name = request.POST.get('group_name', '').strip()
        parent_id = request.POST.get('parent_group', '')
        if name:
            parent = Group.objects.filter(id=parent_id).first() if parent_id else None
            group = Group(name=name, parent=parent)
            group.save()
            messages.success(request, f'Group "{group.name}" created successfully.')
            return redirect('schedule_template')
        else:
            messages.error(request, 'Group name is required.')

    groups = sorted(Group.objects.all(), key=lambda g: str(g).lower())
    selected_group_id = request.GET.get('group', '')

    return render(request, 'myapp/schedule_template.html', {
        'time_slots': slots,
        'groups': groups,
        'selected_group_id': selected_group_id,
    })

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            username = User.objects.get(email=email).username
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                request.session['auth_error'] = 'Invalid email or password.'
        except User.DoesNotExist:
            request.session['auth_error'] = 'No account found with that email.'
    return redirect('home')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(email=email).exists():
            request.session['auth_error'] = 'An account with that email already exists.'
        else:
            username = email
            user = User.objects.create_user(username=username, email=email, password=password)
            name_parts = name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.save()
            login(request, user)
            return redirect('home')
    return redirect('home')

def logout_view(request):
    logout(request)
    return redirect('home')