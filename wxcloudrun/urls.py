"""wxcloudrun URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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

from django.urls import path
from django.contrib import admin
from . import views
from . import miniprogram_views

urlpatterns = [
    # 获取主页
    path('', views.index, name='index'),
    # 管理员界面
    path('admin/', admin.site.urls),
    # 登录页面
    path('login/', views.login, name='login'),
    # 小程序接口
    path('api/parent/login/', miniprogram_views.parent_login, name='parent_login'),
    path('api/parent/register/', miniprogram_views.parent_register, name='parent_register'),
    path('api/coach/login/', miniprogram_views.coach_login, name='coach_login'),
]
