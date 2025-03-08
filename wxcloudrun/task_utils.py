from datetime import datetime, timedelta, date
from django.db.models import Max
import logging

logger = logging.getLogger('log')

def get_player_max_streak(player):
    """
    获取队员在所有任务中的最大连续完成天数
    
    Args:
        player: Player对象
    
    Returns:
        int: 最大连续完成天数
    """
    try:
        from .models import Task, TaskCompletion
        
        # 获取队员完成的所有任务记录
        completions = TaskCompletion.objects.filter(
            player=player, 
            verified=True
        ).order_by('completion_date')
        
        if not completions.exists():
            return 0
        
        # 获取队员所有任务的连续天数
        streaks = []
        for task in Task.objects.filter(taskcompletion__player=player).distinct():
            task_streak = task.get_task_streak(player) if hasattr(task, 'get_task_streak') else 0
            streaks.append(task_streak)
        
        # 返回最大连续天数
        return max(streaks) if streaks else 0
    
    except Exception as e:
        logger.error(f"计算最大连续天数出错: {str(e)}")
        return 0
