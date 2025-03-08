import jwt
from django.conf import settings
from django.http import JsonResponse
import logging

# 设置日志
logger = logging.getLogger(__name__)

def verify_parent_token(request):
    """验证家长token的通用函数"""
    auth_header = request.headers.get('Authorization')
    logger.info(f"Auth header received: {auth_header[:20]}...")
    
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f"Invalid auth header format: {auth_header}")
        return None, JsonResponse({'code': 401, 'message': '无效的token格式'}, status=401)
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        logger.info(f"Token decoded successfully for user_id: {payload.get('user_id')}")
        
        # 验证用户类型
        if payload.get('user_type') != 'parent':
            logger.error(f"Invalid user type: {payload.get('user_type')}")
            return None, JsonResponse({'code': 401, 'message': '用户类型错误'}, status=401)
            
        return payload, None
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None, JsonResponse({'code': 401, 'message': 'token已过期'}, status=401)
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return None, JsonResponse({'code': 401, 'message': '无效的token'}, status=401)
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        return None, JsonResponse({'code': 500, 'message': '服务器验证错误'}, status=500)
