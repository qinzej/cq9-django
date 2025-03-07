from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import jwt
from . import settings

@csrf_exempt
@require_http_methods(["POST"])
def verify_token(request):
    try:
        # 从请求头中获取token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未提供token'
            }, status=401)

        # 验证token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return JsonResponse({
                'code': 200,
                'message': 'token有效',
                'data': {
                    'user_id': payload.get('user_id'),
                    'user_type': payload.get('user_type')
                }
            })
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'code': 401,
                'message': 'token已过期'
            }, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)