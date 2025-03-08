from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from .utils.cloud_storage import CloudStorage
import json
import uuid

@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_badge_image(request):
    """管理员上传徽章图片到云存储"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '未找到上传的图片'
            })
        
        image_file = request.FILES['image']
        folder = request.POST.get('folder', 'badges')
        image_type = request.POST.get('type', 'badge')
        
        # 生成唯一文件名
        file_name = f"{image_type}_{uuid.uuid4().hex}{'.png'}"
        
        # 上传到云存储
        image_url = CloudStorage.upload_file(image_file, file_name, folder)
        
        if not image_url:
            return JsonResponse({
                'success': False,
                'message': '图片上传失败'
            })
        
        # 返回图片URL
        return JsonResponse({
            'success': True,
            'url': image_url,
            'message': '图片上传成功'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'上传出错: {str(e)}'
        })
