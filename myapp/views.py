from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import datetime, timedelta, time as time_type
from .models import Class, Group
import json

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
    
    class_errors = request.session.pop('class_errors', [])
    class_form_data = request.session.pop('class_form_data', {})

    selected_group = Group.objects.filter(id=selected_group_id).first() if selected_group_id else None

    # Build a dict of classes per day for the selected group
    classes_by_day = {}
    if selected_group:
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            classes_by_day[day] = list(getattr(selected_group, day).all())

    classes_json = {}
    if selected_group:
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            classes_json[day] = [
                {
                    'name': c.name,
                    'start': c.start_time.strftime('%H:%M'),
                    'end': c.end_time.strftime('%H:%M'),
                }
                for c in getattr(selected_group, day).all()
            ]

    return render(request, 'myapp/schedule_template.html', {
        'time_slots': slots,
        'groups': groups,
        'selected_group_id': selected_group_id,
        'selected_group': selected_group,
        'classes_by_day': classes_by_day,
        'class_errors': class_errors,
        'class_form_data': class_form_data,
        'classes_json': json.dumps(classes_json),
    })


def create_class(request):
    if request.method == 'POST':
        name = request.POST.get('class_name', '').strip()
        day = request.POST.get('day', '')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')
        group_id = request.POST.get('group_id', '')

        errors = []

        if not name:
            errors.append('Class name is required.')
        if day not in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            errors.append('A valid day is required.')

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            if end_time <= start_time:
                errors.append('End time must be after start time.')
            if start_time < time_type(7, 30):
                errors.append('Start time cannot be before 7:30 AM.')
            if end_time > time_type(16, 30):
                errors.append('End time cannot be after 4:30 PM.')
        except ValueError:
            errors.append('Invalid time format.')
            start_time = end_time = None

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            errors.append('Invalid group selected.')
            group = None

        if errors:
            request.session['class_errors'] = errors
            request.session['class_form_data'] = {
                'class_name': name,
                'day': day,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'group_id': group_id,
            }
            return redirect(f'/schedule-template/?group={group_id}')

        # Create the class and add it to the correct day on the group
        new_class = Class(name=name, start_time=start_time, end_time=end_time)
        new_class.save()
        getattr(group, day).add(new_class)

        return redirect(f'/schedule-template/?group={group_id}')

    return redirect('schedule_template')

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