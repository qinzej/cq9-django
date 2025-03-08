import json
import logging
from django.db.models import Count, Q, F, Exists, OuterRef
from django.utils import timezone
from datetime import date, timedelta
from .models import (
    PersonalAchievement, PlayerAchievement, Player, 
    TaskCompletion, Task, AssessmentScore
)

# 设置日志
logger = logging.getLogger(__name__)

def check_all_achievements():
    """检查所有队员的所有成就"""
    logger.info("开始检查所有队员的成就")
    players = Player.objects.all()
    
    for player in players:
        check_player_achievements(player.id)
    
    logger.info("所有队员的成就检查完成")
    return True

def check_player_achievements(player_id):
    """检查指定队员的所有成就"""
    try:
        player = Player.objects.get(id=player_id)
        
        # 检查任务相关成就
        check_task_achievements(player_id)
        
        # 检查考核相关成就
        check_assessment_achievements(player_id)
        
        # 检查连续/累计相关成就
        check_streak_achievements(player_id)
        
        # 检查特殊成就
        check_special_achievements(player_id)
        
        logger.info(f"队员 {player.name}(ID:{player_id}) 的成就检查完成")
        return True
        
    except Player.DoesNotExist:
        logger.error(f"队员ID {player_id} 不存在")
        return False
    except Exception as e:
        logger.error(f"检查队员ID {player_id} 成就时出错: {str(e)}")
        return False

def check_task_achievements(player_id):
    """检查任务相关成就"""
    try:
        # 获取所有基于任务的自动成就
        task_achievements = PersonalAchievement.objects.filter(
            criteria_type='auto_task',
            is_public=True
        )
        
        player = Player.objects.get(id=player_id)
        
        for achievement in task_achievements:
            try:
                # 如果已经获得此成就，跳过
                if PlayerAchievement.objects.filter(player=player, achievement=achievement).exists():
                    continue
                    
                # 解析条件值
                criteria_dict = json.loads(achievement.criteria_value or '{}')
                task_type = criteria_dict.get('type')
                
                # 根据不同条件类型处理
                if task_type == 'completion_count':
                    # 按完成任务数量颁发成就
                    task_count = int(criteria_dict.get('count', 0))
                    completed_tasks = TaskCompletion.objects.filter(
                        player=player, 
                        verified=True
                    ).values('task').distinct().count()
                    
                    # 更新进度
                    progress = min(100, int(completed_tasks / task_count * 100))
                    
                    # 检查是否达成
                    if completed_tasks >= task_count:
                        _award_achievement(player, achievement)
                    else:
                        # 记录进度
                        _update_achievement_progress(player, achievement, progress)
                        
                elif task_type == 'consecutive_days':
                    # 按连续完成天数颁发成就
                    consecutive_days = int(criteria_dict.get('consecutive_days', 0))
                    
                    # 获取队员所有任务的最大连续天数
                    max_streak = 0
                    for task in Task.objects.filter(period='daily'):
                        streak = task.get_task_streak(player)
                        if streak > max_streak:
                            max_streak = streak
                    
                    # 更新进度
                    progress = min(100, int(max_streak / consecutive_days * 100))
                    
                    # 检查是否达成
                    if max_streak >= consecutive_days:
                        _award_achievement(player, achievement)
                    else:
                        # 记录进度
                        _update_achievement_progress(player, achievement, progress)
                
                # 可以添加更多成就类型处理...
                
            except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
                logger.error(f"处理成就 {achievement.id} ({achievement.name}) 时出错: {str(e)}")
                continue
                
        return True
        
    except Exception as e:
        logger.error(f"检查任务成就时出错: {str(e)}")
        return False

def check_assessment_achievements(player_id):
    """检查考核相关成就"""
    try:
        # 获取所有基于考核的自动成就
        assessment_achievements = PersonalAchievement.objects.filter(
            criteria_type='auto_assessment',
            is_public=True
        )
        
        player = Player.objects.get(id=player_id)
        
        for achievement in assessment_achievements:
            try:
                # 如果已经获得此成就，跳过
                if PlayerAchievement.objects.filter(player=player, achievement=achievement).exists():
                    continue
                    
                # 解析条件值
                criteria_dict = json.loads(achievement.criteria_value or '{}')
                assessment_type = criteria_dict.get('type', 'score')
                
                # 处理不同类型的考核成就
                if assessment_type == 'score':
                    # 按分数颁发
                    min_score = float(criteria_dict.get('min_score', 0))
                    
                    # 查询队员的考核分数
                    scores = AssessmentScore.objects.filter(player=player)
                    
                    if criteria_dict.get('all_items', False):
                        # 要求所有考核项目都达到分数
                        all_passed = scores.count() > 0
                        for score in scores:
                            if score.score < min_score:
                                all_passed = False
                                break
                                
                        if all_passed:
                            _award_achievement(player, achievement)
                    else:
                        # 任一考核项目达到分数即可
                        if scores.filter(score__gte=min_score).exists():
                            _award_achievement(player, achievement)
                
                # 更多考核成就处理...
                
            except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
                logger.error(f"处理成就 {achievement.id} ({achievement.name}) 时出错: {str(e)}")
                continue
                
        return True
        
    except Exception as e:
        logger.error(f"检查考核成就时出错: {str(e)}")
        return False

def check_streak_achievements(player_id):
    """检查连续/累计相关成就"""
    # 实现连续登录、累计打卡等成就检查逻辑
    pass

def check_special_achievements(player_id):
    """检查特殊成就，如首次相关、里程碑等"""
    # 实现首次完成任务、特定日期打卡等特殊成就
    pass

def _award_achievement(player, achievement):
    """为玩家颁发成就"""
    # 检查是否已经颁发过
    if not PlayerAchievement.objects.filter(player=player, achievement=achievement).exists():
        # 创建新的成就记录
        PlayerAchievement.objects.create(
            player=player,
            achievement=achievement,
            progress=100,  # 完全解锁
            # awarded_by 为 None 表示自动颁发
        )
        logger.info(f"成就 '{achievement.name}' 已授予队员 {player.name}(ID:{player.id})")
        return True
    return False

def _update_achievement_progress(player, achievement, progress):
    """更新队员成就进度"""
    # 检查是否已有进度记录
    achievement_record, created = PlayerAchievement.objects.get_or_create(
        player=player,
        achievement=achievement,
        defaults={'progress': progress}
    )
    
    # 如果已存在且进度有提升，则更新
    if not created and achievement_record.progress < progress:
        achievement_record.progress = progress
        achievement_record.save()
        logger.info(f"队员 {player.name}(ID:{player.id}) 的成就 '{achievement.name}' 进度更新为 {progress}%")
    
    return True

def get_recent_achievements(days=7):
    """获取最近几天的成就解锁记录"""
    recent_date = date.today() - timedelta(days=days)
    return PlayerAchievement.objects.filter(
        awarded_date__gte=recent_date
    ).select_related('player', 'achievement').order_by('-awarded_date')

def get_leaderboard():
    """获取成就积分排行榜"""
    return Player.objects.annotate(
        total_points=Sum(
            F('achievements__achievement__points'),
            filter=Q(achievements__progress=100)
        )
    ).filter(total_points__gt=0).order_by('-total_points')[:50]
