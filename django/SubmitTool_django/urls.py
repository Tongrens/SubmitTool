"""
URL configuration for SubmitTool_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, re_path
from . import login, dashboard

urlpatterns = [
    path('', login.login_page),
    path('login/', login.login_page),
    re_path(r'check_qr_login/$', login.check_qr_login),
    re_path(r'check_phone_login/$', login.check_phone_login),
    re_path(r'^dashboard/$', dashboard.get_history_data),
    path('submit/', dashboard.put_info),
]
