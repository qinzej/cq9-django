from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Parent, Coach
import json
import jwt
from datetime import datetime, timedelta
from django.conf import settings

def generate_token(user_id, user_type):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(days=30)  # token有效期30天
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

@csrf_exempt
@require_http_methods(["POST"])
def parent_login(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        password = data.get('password')

        if not phone or not password:
            return JsonResponse({
                'code': 400,
                'message': '手机号和密码不能为空'
            }, status=400)

        # 查找家长
        try:
            parent = Parent.objects.get(phone=phone)
        except Parent.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '该手机号未注册'
            }, status=404)

        # 验证密码
        if parent.miniprogram_password != password:
            return JsonResponse({
                'code': 401,
                'message': '密码错误'
            }, status=401)

        # 生成token
        token = generate_token(parent.id, 'parent')

        # 获取关联的队员信息
        players = [{
            'id': player.id,
            'name': player.name,
            'school': player.school,
            'enrollment_year': player.enrollment_year
        } for player in parent.players.all()]

        # 登录成功，返回家长信息和token
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': parent.id,
                    'name': parent.name,
                    'phone': parent.phone,
                    'type': 'parent',
                    'players': players
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def coach_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                'code': 400,
                'message': '用户名和密码不能为空'
            }, status=400)

        # 验证教练用户
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({
                'code': 401,
                'message': '用户名或密码错误'
            }, status=401)

        # 检查用户是否是教练
        try:
            coach = Coach.objects.get(user=user)
            if not coach.is_active:
                return JsonResponse({
                    'code': 403,
                    'message': '该账号已被禁用'
                }, status=403)
        except Coach.DoesNotExist:
            return JsonResponse({
                'code': 403,
                'message': '该用户不是教练'
            }, status=403)

        # 生成token
        token = generate_token(coach.id, 'coach')

        # 登录成功，返回教练信息和token
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': coach.id,
                    'username': user.username,
                    'name': user.get_full_name() or user.username,
                    'phone': coach.phone,
                    'type': 'coach',
                    'speciality': coach.speciality
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)