import os
import uuid
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import requests
    import json
except ImportError:
    logger.error("requests 库未安装。请运行 `pip install requests` 安装此依赖。")
    requests = None

class CloudStorage:
    """微信云存储工具类"""
    
    # 微信云开发对象存储信息
    BUCKET = '7072-prod-9g1ksrgj4afc4ff1-1345213190'
    REGION = 'ap-shanghai'
    BASE_URL = f'https://{BUCKET}.cos.{REGION}.myqcloud.com'
    
    @staticmethod
    def upload_file(file_content, file_name=None, folder='badges'):
        """
        上传文件到微信云存储
        
        Args:
            file_content: 文件内容（字节流）
            file_name: 文件名，如不提供则自动生成
            folder: 存储目录，默认为'badges'
            
        Returns:
            成功返回文件访问URL，失败返回None
        """
        # 检查requests库是否可用
        if requests is None:
            logger.error("requests 库未安装，无法执行上传操作")
            return None
            
        try:
            # 生成唯一文件名
            if not file_name:
                ext = os.path.splitext(getattr(file_content, 'name', ''))[1] or '.png'
                file_name = f"{uuid.uuid4().hex}{ext}"
            
            # 构建对象存储路径
            object_key = f'{folder}/{file_name}'
            
            # 构建上传URL
            upload_url = f'{CloudStorage.BASE_URL}/{object_key}'
            
            # 上传文件
            if hasattr(file_content, 'read'):
                # 如果是文件对象
                content = file_content.read()
            else:
                # 如果是字节内容
                content = file_content
                
            headers = {'Content-Type': 'application/octet-stream'}
            response = requests.put(upload_url, data=content, headers=headers)
            
            if response.status_code == 200:
                # 返回可访问的URL
                return upload_url
            else:
                logger.error(f"文件上传失败: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            return None
            
    @staticmethod
    def delete_file(file_url):
        """
        从微信云存储删除文件
        
        Args:
            file_url: 文件URL
            
        Returns:
            成功返回True，失败返回False
        """
        # 检查requests库是否可用
        if requests is None:
            logger.error("requests 库未安装，无法执行删除操作")
            return False
            
        try:
            # 从URL中提取对象键
            object_key = file_url.replace(f'{CloudStorage.BASE_URL}/', '')
            
            # 构建删除URL
            delete_url = f'{CloudStorage.BASE_URL}/{object_key}'
            
            # 删除文件
            response = requests.delete(delete_url)
            
            return response.status_code == 204 or response.status_code == 200
                
        except Exception as e:
            logger.error(f"文件删除异常: {str(e)}")
            return False
