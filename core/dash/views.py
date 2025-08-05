from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .models import Group, GroupMember, Task, TaskSubmission, TaskFile

def Landing_page(request):
    return render(request, 'index.html')

def Register(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        company = request.POST['company']
        password = request.POST['password']
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'signup.html')
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name.split()[0],
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
        )
        messages.success(request, 'Account created successfully')
        return redirect('login')
    
    return render(request, 'signup.html')

def LogIn(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'login.html')

@login_required
def dashboard(request):
    user_groups = GroupMember.objects.filter(user=request.user).select_related('group')
    admin_groups = Group.objects.filter(admin=request.user)
    recent_tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')[:5]
    
    context = {
        'user_groups': user_groups,
        'admin_groups': admin_groups,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'dashboard.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        
        group = Group.objects.create(
            name=name,
            description=description,
            admin=request.user
        )
        GroupMember.objects.create(group=group, user=request.user)
        messages.success(request, f'Group "{name}" created successfully!')
        return redirect('group_detail', group_id=group.id)
    
    return render(request, 'create_group.html')

@login_required
def join_group(request):
    if request.method == 'POST':
        code = request.POST['code'].upper()
        
        try:
            group = Group.objects.get(code=code)
            if GroupMember.objects.filter(group=group, user=request.user).exists():
                messages.warning(request, 'You are already a member of this group')
            else:
                GroupMember.objects.create(group=group, user=request.user)
                messages.success(request, f'Successfully joined "{group.name}"!')
                return redirect('group_detail', group_id=group.id)
        except Group.DoesNotExist:
            messages.error(request, 'Invalid group code')
    
    return render(request, 'join_group.html')

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if not GroupMember.objects.filter(group=group, user=request.user).exists():
        messages.error(request, 'You are not a member of this group')
        return redirect('dashboard')
    
    members = GroupMember.objects.filter(group=group).select_related('user')
    tasks = Task.objects.filter(group=group).order_by('-created_at')
    
    context = {
        'group': group,
        'members': members,
        'tasks': tasks,
        'is_admin': group.admin == request.user,
    }
    return render(request, 'group_detail.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('Landing_page')

@login_required
def add_task(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if group.admin != request.user:
        messages.error(request, 'Only group admin can add tasks')
        return redirect('group_detail', group_id=group_id)
    
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        assigned_to_id = request.POST['assigned_to']
        due_date = request.POST.get('due_date')
        
        assigned_user = get_object_or_404(User, id=assigned_to_id)
        
        task = Task.objects.create(
            title=title,
            description=description,
            group=group,
            assigned_to=assigned_user,
            assigned_by=request.user,
            due_date=due_date if due_date else None
        )
        
        messages.success(request, f'Task "{title}" assigned to {assigned_user.first_name}')
        return redirect('group_detail', group_id=group_id)
    
    members = GroupMember.objects.filter(group=group).select_related('user')
    context = {'group': group, 'members': members}
    return render(request, 'add_task.html', context)

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if not GroupMember.objects.filter(group=task.group, user=request.user).exists():
        messages.error(request, 'You are not a member of this group')
        return redirect('dashboard')
    
    files = TaskFile.objects.filter(task=task)
    context = {
        'task': task,
        'files': files,
        'is_assigned': task.assigned_to == request.user,
        'is_admin': task.group.admin == request.user,
    }
    return render(request, 'task_detail.html', context)

@login_required
def submit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if task.assigned_to != request.user:
        messages.error(request, 'You can only submit your own tasks')
        return redirect('task_detail', task_id=task_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        files = request.FILES.getlist('files')
        
        # Create or update submission
        submission, created = TaskSubmission.objects.get_or_create(
            task=task,
            defaults={'submitted_by': request.user, 'notes': notes}
        )
        
        if not created:
            submission.notes = notes
            submission.save()
        
        # Handle file uploads
        for file in files:
            TaskFile.objects.create(
                task=task,
                file=file,
                uploaded_by=request.user
            )
        
        task.status = 'submitted'
        task.save()
        
        messages.success(request, 'Task submitted for approval')
        return redirect('task_detail', task_id=task_id)
    
    return redirect('task_detail', task_id=task_id)

@login_required
def approve_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if task.group.admin != request.user:
        messages.error(request, 'Only group admin can approve tasks')
        return redirect('task_detail', task_id=task_id)
    
    task.status = 'completed'
    task.save()
    
    messages.success(request, f'Task "{task.title}" approved and completed')
    return redirect('task_detail', task_id=task_id)

@login_required
def reject_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if task.group.admin != request.user:
        messages.error(request, 'Only group admin can reject tasks')
        return redirect('task_detail', task_id=task_id)
    
    task.status = 'rejected'
    task.save()
    
    messages.warning(request, f'Task "{task.title}" rejected')
    return redirect('task_detail', task_id=task_id)