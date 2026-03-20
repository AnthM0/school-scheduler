from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta, time as time_type
from ..models import Class, Group
import json


# ── Helpers ────────────────────────────────────────────────────────────────────

def build_time_slots():
    """
    Generates a list of time slot dicts from 7:30 AM to 4:30 PM
    in 30-minute increments, used to render the schedule grid rows
    and populate the time dropdowns in the class modal.
    """
    slots   = []
    start   = datetime.strptime('7:30 AM', '%I:%M %p')
    end     = datetime.strptime('4:30 PM', '%I:%M %p')
    current = start

    while current <= end:
        slots.append({
            'label':      current.strftime('%I:%M %p').lstrip('0'),
            'value':      current.strftime('%H:%M'),
            'is_half':    current.minute == 30,
            'show_label': current.minute % 30 == 0,
        })
        current += timedelta(minutes=30)

    return slots


def get_classes_for_group(group):
    """
    Returns a dict of { day: [class_data, ...] } for the given group,
    including classes inherited from all ancestor groups up the parent chain.
    Each class dict includes all fields needed for rendering and editing.
    """
    days          = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    classes_by_day = {day: [] for day in days}

    # Walk up the parent chain, collecting all groups
    groups_in_chain = []
    current         = group
    while current is not None:
        groups_in_chain.append(current)
        current = current.parent

    # Merge classes from every group in the chain into the result
    for g in groups_in_chain:
        for day in days:
            for c in getattr(g, day).all():
                classes_by_day[day].append({
                    'id':       c.id,
                    'name':     c.name,
                    'subject':  c.subject,
                    'start':    c.start_time.strftime('%H:%M'),
                    'end':      c.end_time.strftime('%H:%M'),
                    'group':    g.name,
                    'group_id': g.id,
                    'day':      day,
                })

    return classes_by_day


def validate_class_times(start_str, end_str):
    """
    Parses and validates start/end time strings (format: HH:MM).
    Returns (start_time, end_time, errors) where errors is a list of
    human-readable error strings. Times must be between 7:30 AM and 4:30 PM.
    """
    errors     = []
    start_time = None
    end_time   = None

    try:
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time   = datetime.strptime(end_str,   '%H:%M').time()

        if end_time <= start_time:
            errors.append('End time must be after start time.')
        if start_time < time_type(7, 30):
            errors.append('Start time cannot be before 7:30 AM.')
        if end_time > time_type(16, 30):
            errors.append('End time cannot be after 4:30 PM.')
    except ValueError:
        errors.append('Invalid time format.')

    return start_time, end_time, errors


# ── Views ──────────────────────────────────────────────────────────────────────

def schedule_template(request):
    """
    Main schedule page. Handles two responsibilities:
      1. Rendering the schedule grid with classes for the selected group.
      2. Processing the Create Group form submission from the group modal.
    """

    # ── Handle create group form submission ──
    if request.method == 'POST' and 'create_group' in request.POST:
        name      = request.POST.get('group_name', '').strip()
        parent_id = request.POST.get('parent_group', '')

        if name:
            parent = Group.objects.filter(id=parent_id).first() if parent_id else None
            group  = Group(name=name, parent=parent)
            group.save()
        else:
            messages.error(request, 'Group name is required.')

        return redirect('schedule_template')

    # ── Build context for rendering ──
    slots            = build_time_slots()
    groups           = sorted(Group.objects.all(), key=lambda g: str(g).lower())
    selected_group_id = request.GET.get('group', '')
    selected_group   = Group.objects.filter(id=selected_group_id).first() if selected_group_id else None

    # Pop any class form errors/data stored in the session by create_class/edit_class
    class_errors    = request.session.pop('class_errors',    [])
    class_form_data = request.session.pop('class_form_data', {})

    # Serialize the selected group's classes (including inherited) to JSON for the grid
    classes_json = get_classes_for_group(selected_group) if selected_group else {}

    return render(request, 'myapp/schedule_template.html', {
        'time_slots':       slots,
        'groups':           groups,
        'selected_group_id': selected_group_id,
        'selected_group':   selected_group,
        'class_errors':     class_errors,
        'class_form_data':  class_form_data,
        'classes_json':     json.dumps(classes_json),
    })


def create_class(request):
    """
    Handles new class creation from the class modal form.
    Validates all fields, creates the Class object, and assigns it
    to the correct weekday field on the selected Group.
    On error: stores errors in the session and redirects back to the schedule page.
    """
    if request.method == 'POST':
        name          = request.POST.get('class_name', '').strip()
        subject       = request.POST.get('subject', 'other').strip() or 'other'
        day           = request.POST.get('day', '')
        start_str     = request.POST.get('start_time', '')
        end_str       = request.POST.get('end_time', '')
        group_id      = request.POST.get('group_id', '')

        errors = []

        if not name:
            errors.append('Class name is required.')
        if day not in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            errors.append('A valid day is required.')

        start_time, end_time, time_errors = validate_class_times(start_str, end_str)
        errors.extend(time_errors)

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            errors.append('Invalid group selected.')
            group = None

        if errors:
            request.session['class_errors']    = errors
            request.session['class_form_data'] = {
                'class_name': name, 'day': day,
                'start_time': start_str, 'end_time': end_str,
                'group_id':   group_id,
            }
            return redirect(f'/schedule-template/?group={group_id}')

        # Save the class and link it to the correct day on the group
        new_class = Class(name=name, subject=subject, start_time=start_time, end_time=end_time)
        new_class.save()
        getattr(group, day).add(new_class)

        return redirect(f'/schedule-template/?group={group_id}')

    return redirect('schedule_template')


def edit_class(request, class_id):
    """
    Handles editing an existing class from the class modal.
    Removes the class from its current weekday slot on the group,
    updates all fields, then re-adds it to the (potentially new) weekday slot.
    On error: stores errors in the session and redirects back to the schedule page.
    """
    try:
        existing_class = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        return redirect('schedule_template')

    group_id = request.POST.get('group_id', '') or request.GET.get('group', '')

    if request.method == 'POST':
        name      = request.POST.get('class_name', '').strip()
        subject   = request.POST.get('subject', 'other').strip() or 'other'
        day       = request.POST.get('day', '')
        start_str = request.POST.get('start_time', '')
        end_str   = request.POST.get('end_time', '')

        errors = []

        if not name:
            errors.append('Class name is required.')
        if day not in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            errors.append('A valid day is required.')

        start_time, end_time, time_errors = validate_class_times(start_str, end_str)
        errors.extend(time_errors)

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            errors.append('Invalid group selected.')
            group = None

        if errors:
            request.session['class_errors']    = errors
            request.session['class_form_data'] = {
                'class_name': name, 'day': day,
                'start_time': start_str, 'end_time': end_str,
                'group_id':   group_id, 'edit_id': class_id,
            }
            return redirect(f'/schedule-template/?group={group_id}')

        # Remove the class from all weekday slots on this group before re-adding
        if group:
            for d in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                getattr(group, d).remove(existing_class)

        # Update and save the class fields
        existing_class.name       = name
        existing_class.subject    = subject
        existing_class.start_time = start_time
        existing_class.end_time   = end_time
        existing_class.save()

        # Re-add to the correct (possibly changed) weekday
        if group:
            getattr(group, day).add(existing_class)

        return redirect(f'/schedule-template/?group={group_id}')

    return redirect('schedule_template')


def delete_class(request, class_id):
    """
    Deletes a class by ID.
    Only accepts POST requests. Redirects back to the schedule page
    for the group the class belonged to.
    """
    if request.method == 'POST':
        group_id = request.POST.get('group_id', '')
        try:
            Class.objects.get(id=class_id).delete()
        except Class.DoesNotExist:
            pass
        return redirect(f'/schedule-template/?group={group_id}')

    return redirect('schedule_template')