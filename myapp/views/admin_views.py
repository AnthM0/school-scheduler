from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from ..models import UserProfile, Group


def users_and_permissions(request):
    """
    Renders the Users and Permissions page.
    Handles both new user creation and new group creation.
    """

    # ── Handle create user ──
    if request.method == 'POST' and 'create_user' in request.POST:
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        email      = request.POST.get('email',      '').strip()
        password   = request.POST.get('password',   '').strip()
        role       = request.POST.get('role',       'student')
        group_id   = request.POST.get('group',      '')

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('A user with that email already exists.')
        if not password:
            errors.append('Password is required.')
        if role not in ['superuser', 'admin', 'teacher', 'student']:
            errors.append('Invalid role selected.')

        if errors:
            request.session['user_errors']    = errors
            request.session['user_form_data'] = {
                'first_name': first_name, 'last_name': last_name,
                'email': email, 'role': role, 'group': group_id,
            }
            return redirect('users_and_permissions')

        user            = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = first_name
        user.last_name  = last_name
        if role == 'superuser':
            user.is_staff     = True
            user.is_superuser = True
        user.save()

        group = None
        if role in ['teacher', 'student'] and group_id:
            group = Group.objects.filter(id=group_id).first()

        UserProfile.objects.create(user=user, role=role, group=group)
        return redirect('users_and_permissions')

    # ── Handle create group ──
    if request.method == 'POST' and 'create_group' in request.POST:
        name      = request.POST.get('group_name',   '').strip()
        parent_id = request.POST.get('parent_group', '')

        if not name:
            request.session['group_errors']    = ['Group name is required.']
            request.session['group_form_data'] = {'parent_group': parent_id}
            return redirect('users_and_permissions')

        parent = Group.objects.filter(id=parent_id).first() if parent_id else None
        group  = Group(name=name, parent=parent)
        group.save()
        return redirect('users_and_permissions')

    # ── Build context ──
    user_errors     = request.session.pop('user_errors',     [])
    user_form_data  = request.session.pop('user_form_data',  {})
    group_errors    = request.session.pop('group_errors',    [])
    group_form_data = request.session.pop('group_form_data', {})
    edit_user_errors     = request.session.pop('edit_user_errors',     [])
    edit_user_form_data  = request.session.pop('edit_user_form_data',  {})
    edit_group_errors    = request.session.pop('edit_group_errors',    [])
    edit_group_form_data = request.session.pop('edit_group_form_data', {})
    
    ROLE_ORDER = {'superuser': 0, 'admin': 1, 'teacher': 2, 'student': 3}
    users = sorted(
        UserProfile.objects.all().select_related('user', 'group'),
        key=lambda p: (
            ROLE_ORDER.get(p.role, 99),
            str(p.group).lower() if p.group else '',
            p.user.last_name.lower(),
            p.user.first_name.lower(),
        )
    )
    groups          = sorted(Group.objects.all(), key=lambda g: str(g).lower())

    return render(request, 'myapp/users_and_permissions.html', {
        'users':           users,
        'groups':          groups,
        'user_errors':     user_errors,
        'user_form_data':  user_form_data,
        'group_errors':    group_errors,
        'group_form_data': group_form_data,
        'edit_user_errors':     edit_user_errors,
        'edit_user_form_data':  edit_user_form_data,
        'edit_group_errors':    edit_group_errors,
        'edit_group_form_data': edit_group_form_data,
    })


def edit_user(request, user_id):
    """
    Handles editing an existing user.
    The currently logged-in user cannot edit their own account.
    Password is only updated if a new one is provided.
    """
    # Prevent editing your own account
    if request.user.id == user_id:
        return redirect('users_and_permissions')

    try:
        target_user = User.objects.get(id=user_id)
        profile     = target_user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return redirect('users_and_permissions')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        email      = request.POST.get('email',      '').strip()
        password   = request.POST.get('password',   '').strip()
        role       = request.POST.get('role',       'student')
        group_id   = request.POST.get('group',      '')

        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append('Another user with that email already exists.')
        if role not in ['superuser', 'admin', 'teacher', 'student']:
            errors.append('Invalid role selected.')

        if errors:
            request.session['edit_errors']    = errors
            request.session['edit_form_data'] = {
                'user_id':    user_id,
                'first_name': first_name, 'last_name': last_name,
                'email':      email,      'role':      role,
                'group':      group_id,
            }
            return redirect('users_and_permissions')

        # Update user fields
        target_user.first_name = first_name
        target_user.last_name  = last_name
        target_user.email      = email
        target_user.username   = email
        target_user.is_staff     = (role == 'superuser')
        target_user.is_superuser = (role == 'superuser')
        if password:
            target_user.set_password(password)
        target_user.save()

        # Update profile
        group = None
        if role in ['teacher', 'student'] and group_id:
            group = Group.objects.filter(id=group_id).first()
        profile.role  = role
        profile.group = group
        profile.save()

        return redirect('users_and_permissions')

    return redirect('users_and_permissions')


def delete_user(request, user_id):
    """
    Deletes a user by ID.
    The currently logged-in user cannot delete their own account.
    """
    if request.user.id == user_id:
        return redirect('users_and_permissions')

    if request.method == 'POST':
        try:
            User.objects.get(id=user_id).delete()
        except User.DoesNotExist:
            pass

    return redirect('users_and_permissions')

def edit_group(request, group_id):
    """
    Handles editing an existing group's name and parent.
    """
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return redirect('users_and_permissions')

    if request.method == 'POST':
        name      = request.POST.get('group_name', '').strip()
        parent_id = request.POST.get('parent_group', '')

        if not name:
            request.session['edit_group_errors']    = ['Group name is required.']
            request.session['edit_group_form_data'] = {
                'group_id':     group_id,
                'group_name':   name,
                'parent_group': parent_id,
            }
            return redirect('users_and_permissions')

        # Prevent a group from being its own parent
        parent = None
        if parent_id and int(parent_id) != group_id:
            parent = Group.objects.filter(id=parent_id).first()

        group.name   = name
        group.parent = parent
        group.save()

        return redirect('users_and_permissions')

    return redirect('users_and_permissions')


def delete_group(request, group_id):
    """
    Deletes a group by ID.
    """
    if request.method == 'POST':
        try:
            Group.objects.get(id=group_id).delete()
        except Group.DoesNotExist:
            pass

    return redirect('users_and_permissions')