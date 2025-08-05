"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from dash.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Landing_page, name="Landing_page"),
    path('signup/', Register, name="signup"),
    path('login/', LogIn, name="login"),
    path('logout/', logout_view, name="logout"),
    path('dashboard/', dashboard, name="dashboard"),
    path('create-group/', create_group, name="create_group"),
    path('join-group/', join_group, name="join_group"),
    path('group/<int:group_id>/', group_detail, name="group_detail"),
    path('group/<int:group_id>/add-task/', add_task, name="add_task"),
    path('task/<int:task_id>/', task_detail, name="task_detail"),
    path('task/<int:task_id>/submit/', submit_task, name="submit_task"),
    path('task/<int:task_id>/approve/', approve_task, name="approve_task"),
    path('task/<int:task_id>/reject/', reject_task, name="reject_task"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
