import json
import logging
import jwt  # Add this import for JWT functions
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings  # Add this import for settings
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Parent, Player  # Add models import

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

# 检查绑定队员的API视图
@csrf_exempt
@require_http_methods(["POST"])
def bind_player(request):
    # ...existing code...
    
    # 验证队员是否已被该家长绑定
    if Parent.objects.filter(id=parent_id, players__id=player_id).exists():
        return JsonResponse({'code': 400, 'message': '您已经绑定过该队员'}, status=400)
    
    # 获取家长和队员对象
    try:
        parent = Parent.objects.get(id=parent_id)
        player = Player.objects.get(id=player_id)
    except (Parent.DoesNotExist, Player.DoesNotExist):
        return JsonResponse({'code': 404, 'message': '家长或队员不存在'}, status=404)
    
    # 添加关联 - 这里应该正确使用多对多关系方法
    parent.players.add(player)
    # ...existing code...

# 检查解绑队员的API视图
@csrf_exempt
@require_http_methods(["POST"])
def unbind_player(request):
    # ...existing code...
    
    # 验证队员是否属于该家长
    try:
        parent = Parent.objects.get(id=parent_id)
        player = Player.objects.get(id=player_id)
        
        # 验证关联
        if not parent.players.filter(id=player_id).exists():
            return JsonResponse({'code': 403, 'message': '您未绑定该队员'}, status=403)
        
        # 移除关联
        parent.players.remove(player)
        # ...existing code...
    except (Parent.DoesNotExist, Player.DoesNotExist):
        return JsonResponse({'code': 404, 'message': '家长或队员不存在'}, status=404)
    # ...existing code...

# 检查家长登录时的用户信息返回
@csrf_exempt
@require_http_methods(["POST"])
def parent_login(request):
    # ...existing code...
    
    # 获取该家长绑定的队员列表
    players_data = []
    for player in parent.players.all():  # 正确使用多对多关系的查询
        players_data.append({
            'id': player.id,
            'name': player.name,
            # ...other player fields...
        })
    # ...existing code...

@csrf_exempt
@require_http_methods(["GET"])
def get_parent_players(request):
    """获取家长绑定的队员列表"""
    # 验证token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return JsonResponse({'code': 401, 'message': '无效的token格式'}, status=401)
    
    token = auth_header.split(' ')[1]
    
    try:
        # 解码token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        
        # 验证用户类型
        if payload.get('user_type') != 'parent':
            return JsonResponse({'code': 401, 'message': '用户类型错误'}, status=401)
            
        parent_id = payload.get('user_id')
        
        # 获取家长
        try:
            parent = Parent.objects.get(id=parent_id)
        except Parent.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '家长不存在'}, status=404)
        
        # 获取绑定的队员列表
        players_data = []
        for player in parent.players.all():
            players_data.append({
                'id': player.id,
                'name': player.name,
                'jersey_number': player.jersey_number,
                'school': {
                    'id': player.school.id,
                    'name': player.school.name
                } if player.school else None,
                'enrollment_year': {
                    'id': player.enrollment_year.id,
                    'year': player.enrollment_year.year
                } if player.enrollment_year else None,
                'avatar': player.avatar,
                'teams': [{'id': team.id, 'name': team.name} for team in player.teams.all()]
            })
        
        return JsonResponse({
            'code': 200,
            'message': '获取成功',
            'data': {
                'players': players_data
            }
        })
    except jwt.ExpiredSignatureError:
        return JsonResponse({'code': 401, 'message': 'token已过期'}, status=401)
    except jwt.InvalidTokenError:
        return JsonResponse({'code': 401, 'message': '无效的token'}, status=401)
    except Exception as e:
        logger.error(f"获取队员列表错误: {str(e)}")
        return JsonResponse({'code': 500, 'message': '服务器错误'}, status=500)
