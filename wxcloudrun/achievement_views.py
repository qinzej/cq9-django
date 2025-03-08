from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from .models import PersonalAchievement, PlayerAchievement, AchievementCategory

@staff_member_required
def achievement_dashboard(request):
    """成就体系管理仪表盘"""
    # 获取统计信息
    achievement_count = PersonalAchievement.objects.count()
    unlocked_count = PlayerAchievement.objects.filter(progress=100).count()
    category_stats = AchievementCategory.objects.annotate(
        total=Count('personal_achievements'),
        unlocked=Count('personal_achievements__player_records', 
                     filter=Q(personal_achievements__player_records__progress=100))
    )
    
    # 渲染仪表盘
    context = {
        'achievement_count': achievement_count,
        'unlocked_count': unlocked_count,
        'category_stats': category_stats,
        'title': '成就体系仪表盘'
    }
    return render(request, 'admin/achievement_dashboard.html', context)