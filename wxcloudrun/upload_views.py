import os
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import jwt
from datetime import datetime
from django.conf import settings

@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    """处理图片上传，返回图片URL"""
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 检查是否有上传文件
        if 'file' not in request.FILES:
            return JsonResponse({
                'code': 400,
                'message': '没有上传文件'
            }, status=400)

        image_file = request.FILES['file']
        
        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'code': 400,
                'message': '不支持的文件类型，请上传图片文件'
            }, status=400)
            
        # 限制文件大小（2MB）
        if image_file.size > 2 * 1024 * 1024:
            return JsonResponse({
                'code': 400,
                'message': '文件太大，请上传小于2MB的图片'
            }, status=400)
            
        # 确保上传目录存在
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        ext = os.path.splitext(image_file.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # 保存文件
        with open(filepath, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
                
        # 构建URL路径
        url = f"{settings.MEDIA_URL}avatars/{filename}"
        
        return JsonResponse({
            'code': 200,
            'message': '上传成功',
            'data': {
                'url': url
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'上传失败: {str(e)}'
        }, status=500)
