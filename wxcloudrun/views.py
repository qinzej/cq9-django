import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login

logger = logging.getLogger('log')

def index(request):
    return redirect('login')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('admin:index')
        else:
            return render(request, 'login.html', {'error_message': '用户名或密码错误'})
    
    return render(request, 'login.html')
