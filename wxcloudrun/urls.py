"""wxcloudrun URL Configuration"""

from django.urls import path
from django.contrib import admin
from . import views
from . import miniprogram_views
from . import auth_views
from . import task_views  # 导入任务视图
from . import achievement_views  # 导入成就视图
from . import admin_views  # 导入管理视图
from . import player_views  # 导入新的player_views模块

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
    path('api/schools/', miniprogram_views.get_schools, name='get_schools'),
    path('api/enrollment-years/', miniprogram_views.get_enrollment_years, name='get_enrollment_years'),
    path('api/parent/search_players/', miniprogram_views.search_players, name='search_players'),
    path('api/parent/add_player/', miniprogram_views.add_player, name='add_player'),
    path('api/parent/update_player/', miniprogram_views.update_player, name='update_player'),  # 新增更新队员接口
    path('api/parent/bind_player/', miniprogram_views.bind_player, name='bind_player'),
    path('api/parent/unbind_player/', miniprogram_views.unbind_player, name='unbind_player'),
    path('api/parent/logout/', miniprogram_views.parent_logout, name='parent_logout'),
    path('api/auth/verify/', auth_views.verify_token, name='verify_token'),
    
    # 任务相关接口
    path('api/player/tasks/', task_views.get_player_tasks, name='get_player_tasks'),
    path('api/player/complete_task/', task_views.complete_task, name='complete_task'),
    path('api/player/task_details/', task_views.get_task_details, name='get_task_details'),
    path('api/player/team_task_stats/', task_views.get_team_task_stats, name='get_team_task_stats'),
    path('api/player/task_history/', task_views.get_player_task_history, name='get_player_task_history'),
    path('api/player/update_task_completion/', task_views.update_task_completion_status, name='update_task_completion_status'),
    path('api/coach/assign_task/', task_views.assign_task_to_team, name='assign_task_to_team'),
    
    # 添加调试接口
    path('api/debug/player_tasks/', task_views.debug_player_tasks, name='debug_player_tasks'),
    
    # 成就系统管理相关URL
    # 保留但注释掉成就仪表盘 URL
    # path('admin/achievement/dashboard/', achievement_views.achievement_dashboard, name='achievement_dashboard'),
    
    # 管理员工具API
    path('api/admin/upload_badge/', admin_views.upload_badge_image, name='upload_badge_image'),

    # 在urlpatterns列表中添加:
    path('api/parent/players/', views.get_parent_players, name='get_parent_players'),
    
    # 队员详情API
    path('api/player/details/', player_views.get_player_details, name='get_player_details'),
]

# 这段代码通常不需要修改，因为Django admin会自动处理注册的模型
