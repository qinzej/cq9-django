from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from .models import Player, Team, Task, TaskCompletion, Assessment, AssessmentScore
from .task_views import verify_token_and_get_player
import logging

logger = logging.getLogger('log')

@csrf_exempt
@require_http_methods(["GET"])
def get_player_details(request):
    """获取队员详细信息"""
    player_id = request.GET.get('player_id')
    
    if not player_id:
        return JsonResponse({'code': 400, 'message': '缺少player_id参数'}, status=400)
        
    # 验证token和获取队员
    player, error_response = verify_token_and_get_player(request, player_id)
    if error_response:
        return error_response
    
    # 获取队员所属的队伍
    teams = player.teams.all()
    teams_data = []
    for team in teams:
        # 修复：处理Coach模型可能的不同名称属性
        coach_name = None
        if team.head_coach:
            # 尝试几种可能的名称属性
            if hasattr(team.head_coach, 'coach_name'):
                coach_name = team.head_coach.coach_name
            elif hasattr(team.head_coach, 'full_name'):
                coach_name = team.head_coach.full_name
            elif hasattr(team.head_coach, 'user') and hasattr(team.head_coach.user, 'username'):
                coach_name = team.head_coach.user.username
            else:
                # 最后尝试用字符串表示
                coach_name = str(team.head_coach)
        
        teams_data.append({
            'id': team.id,
            'name': team.name,
            'logo': team.logo_url if hasattr(team, 'logo_url') else None,
            'coach': coach_name,  # 使用安全获取的教练名称
        })
    
    # 获取队员的基础统计信息
    stats = {
        'task_completion_rate': 0,
        'task_streak': 0,
        'achievements_count': 0,
        'assessment_avg_score': 0,
    }
    
    # 尝试获取任务完成情况
    try:
        total_tasks = Task.objects.filter(teams__in=teams).distinct().count()
        completed_tasks = TaskCompletion.objects.filter(
            player=player, 
            verified=True
        ).values('task').distinct().count()
        
        if total_tasks > 0:
            stats['task_completion_rate'] = round((completed_tasks / total_tasks) * 100)
        
        # 获取最长连续完成天数 - 使用try/except避免模块导入错误
        try:
            from .task_utils import get_player_max_streak
            stats['task_streak'] = get_player_max_streak(player)
        except ImportError:
            logger.warning("task_utils模块不可用，无法计算连续天数")
            # 如果不能导入，使用默认值
            stats['task_streak'] = 0
        
    except Exception as e:
        logger.error(f"计算队员任务统计出错: {str(e)}")
    
    # 尝试获取成就数量
    try:
        if hasattr(player, 'achievements'):
            stats['achievements_count'] = player.achievements.filter(progress=100).count()
    except Exception as e:
        logger.error(f"获取队员成就数量出错: {str(e)}")
    
    # 尝试获取考核平均成绩
    try:
        scores = AssessmentScore.objects.filter(player=player)
        if scores.exists():
            avg_score = scores.aggregate(avg=Avg('score'))['avg']
            stats['assessment_avg_score'] = round(avg_score, 1)
    except Exception as e:
        logger.error(f"获取队员考核成绩出错: {str(e)}")
    
    # 组织返回数据
    player_data = {
        'id': player.id,
        'name': player.name,
        'jersey_number': player.jersey_number,
        'avatar': player.avatar,
        'school': {
            'id': player.school.id,
            'name': player.school.name
        } if player.school else None,
        'enrollment_year': {
            'id': player.enrollment_year.id,
            'year': player.enrollment_year.year
        } if player.enrollment_year else None,
        'teams': teams_data,
        'stats': stats,
        'notes': player.notes,
        'created_at': player.created_at.strftime('%Y-%m-%d') if hasattr(player, 'created_at') else None
    }
    
    return JsonResponse({
        'code': 200,
        'message': '获取成功',
        'data': player_data
    })
