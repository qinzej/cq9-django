from datetime import datetime, date
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
import json

# Create your models here.
class School(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='学校名称')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'school'
        verbose_name = '学校'
        verbose_name_plural = '学校'
        ordering = ['name']

class EnrollmentYear(models.Model):
    year = models.IntegerField(unique=True, verbose_name='入学年份')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.year)

    class Meta:
        db_table = 'enrollment_year'
        verbose_name = '入学年份'
        verbose_name_plural = '入学年份'
        ordering = ['-year']

class Coach(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    speciality = models.CharField(max_length=100, blank=True)
    introduction = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = 'coach'
        verbose_name = '教练信息'
        verbose_name_plural = '教练信息'

class Parent(models.Model):
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='手机号')
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name='家长姓名')
    miniprogram_password = models.CharField(max_length=128, blank=True, null=True, verbose_name='小程序登录密码')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name or "未命名"} ({self.phone or "无手机号"})'

    class Meta:
        db_table = 'parent'
        verbose_name = '家长信息'
        verbose_name_plural = '家长信息'

class Player(models.Model):
    name = models.CharField(max_length=50, verbose_name='队员姓名')
    school = models.ForeignKey(School, on_delete=models.PROTECT, verbose_name='所在学校')
    enrollment_year = models.ForeignKey(EnrollmentYear, on_delete=models.PROTECT, verbose_name='入学年份')
    notes = models.TextField(blank=True, verbose_name='备注')
    avatar = models.URLField(max_length=500, blank=True, null=True, verbose_name='头像URL')
    jersey_number = models.CharField(max_length=10, blank=True, null=True, verbose_name='背号')
    parents = models.ManyToManyField(Parent, related_name='players', verbose_name='家长')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def grade(self):
        """根据入学年份计算年级，考虑9月1日的学年切换"""
        if not self.enrollment_year:
            return None
            
        from datetime import datetime, date
        current_date = datetime.now().date()
        current_year = current_date.year
        
        # 计算当前学年，9月1日为学年分界点
        # 如果当前日期早于9月1日，则仍然是上一学年
        if current_date < date(current_year, 9, 1):
            academic_year = current_year - 1
        else:
            academic_year = current_year
            
        # 计算年级（当前学年 - 入学年 + 1）
        grade_number = academic_year - self.enrollment_year.year + 1
        
        # 年级展示的中文名称
        grade_names = {
            1: '一年级', 2: '二年级', 3: '三年级',
            4: '四年级', 5: '五年级', 6: '六年级',
            7: '初一', 8: '初二', 9: '初三',
            10: '高一', 11: '高二', 12: '高三',
        }
        
        return grade_names.get(grade_number, f'第{grade_number}年')

    class Meta:
        db_table = 'player'
        verbose_name = '队员信息'
        verbose_name_plural = '队员信息'

# 队伍管理模块
class Team(models.Model):
    STATUS_CHOICES = (
        ('active', '活跃中'),
        ('disbanded', '已解散'),
    )
    name = models.CharField(max_length=100, verbose_name='队伍名称')
    players = models.ManyToManyField(Player, related_name='teams', verbose_name='队员')
    head_coach = models.ForeignKey(Coach, on_delete=models.PROTECT, related_name='headed_teams', verbose_name='主教练')
    coaches = models.ManyToManyField(Coach, related_name='coached_teams', verbose_name='教练')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'team'
        verbose_name = '队伍'
        verbose_name_plural = '队伍'
        ordering = ['name']

# 队伍成绩记录
class TeamResult(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='results', verbose_name='队伍')
    competition_name = models.CharField(max_length=200, verbose_name='比赛名称')
    competition_date = models.DateField(verbose_name='比赛日期')
    result = models.CharField(max_length=100, verbose_name='成绩')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.team.name} - {self.competition_name} - {self.result}'

    class Meta:
        db_table = 'team_result'
        verbose_name = '队伍成绩'
        verbose_name_plural = '队伍成绩'
        ordering = ['-competition_date']

# 任务管理模块
class TaskType(models.Model):
    """任务类型"""
    name = models.CharField(max_length=50, verbose_name='类型名称')
    description = models.TextField(blank=True, null=True, verbose_name='类型描述')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='图标')
    color = models.CharField(max_length=20, default='#1890ff', verbose_name='颜色')
    
    class Meta:
        verbose_name = '任务类型'
        verbose_name_plural = '任务类型'

    def __str__(self):
        return self.name

class Task(models.Model):
    """任务模型"""
    PERIOD_CHOICES = [
        ('once', '一次性'),
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]
    
    STATUS_CHOICES = [
        ('active', '活跃中'),
        ('completed', '已结束'),
        ('expired', '已过期'),
        ('draft', '草稿'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='任务标题')
    description = models.TextField(verbose_name='任务描述')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='once', verbose_name='频率')
    # 修改为多对多关系
    teams = models.ManyToManyField(Team, related_name='tasks', verbose_name='所属队伍', blank=True)
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    points = models.IntegerField(default=1, verbose_name='积分值')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    require_proof = models.BooleanField(default=False, verbose_name='是否需要证明')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    task_type = models.ForeignKey(TaskType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='任务类型')
    
    class Meta:
        db_table = 'task'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        
    def __str__(self):
        return self.title
    
    def get_completion_rate(self):
        """获取任务完成率"""
        # 获取关联的队伍的队员数量
        team_players_count = Player.objects.count()  # 临时替代方案
        if team_players_count == 0:
            return 0
            
        # 获取当天或总体的完成人数
        if self.period == 'once':
            completed = self.taskcompletion_set.filter(verified=True).values('player').distinct().count()
        else:
            # 对于周期性任务，计算当天的完成率
            today = date.today()
            completed = self.taskcompletion_set.filter(
                completion_date=today,
                verified=True
            ).count()
            
        return round((completed / team_players_count) * 100)
        
    def get_task_streak(self, player):
        """获取指定队员的连续完成天数"""
        if self.period == 'once':
            # 一次性任务没有连续概念
            completion = self.taskcompletion_set.filter(player=player, verified=True).first()
            return 1 if completion else 0
            
        # 查询队员最近的完成记录，按日期倒序排列
        completions = self.taskcompletion_set.filter(
            player=player,
            verified=True
        ).order_by('-completion_date')
        
        if not completions:
            return 0
            
        streak = 0
        last_date = None
        
        for completion in completions:
            current_date = completion.completion_date
            
            # 第一次循环，初始化last_date
            if last_date is None:
                last_date = current_date
                streak = 1
                continue
                
            # 检查日期是否连续
            date_diff = (last_date - current_date).days
            
            if self.period == 'daily' and date_diff == 1:
                streak += 1
            elif self.period == 'weekly' and date_diff <= 7 and current_date.weekday() == last_date.weekday():
                streak += 1
            elif self.period == 'monthly' and current_date.month == (last_date.month - 1) % 12:
                streak += 1
            else:
                break
                
            last_date = current_date
            
        return streak

class TaskCompletion(models.Model):
    """任务完成记录"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name='关联任务')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='完成队员')
    completion_date = models.DateField(verbose_name='完成日期')
    proof = models.CharField(max_length=100, null=True, blank=True, verbose_name='证明')
    notes = models.TextField(verbose_name='备注')
    verified = models.BooleanField(default=False, verbose_name='是否已验证')
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='验证人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'task_completion'
        verbose_name = '任务完成记录'
        verbose_name_plural = '任务完成记录'
        unique_together = ['task', 'player', 'completion_date']
        ordering = ['-completion_date']
    
    def __str__(self):
        return f"{self.player.name} - {self.task.title} - {self.completion_date}"

class Assessment(models.Model):
    """考核模型"""
    name = models.CharField(max_length=100, verbose_name='考核名称')
    description = models.TextField(blank=True, verbose_name='考核描述')
    teams = models.ManyToManyField(Team, related_name='assessments', verbose_name='参与队伍')
    assessment_date = models.DateField(verbose_name='考核日期')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'assessment'
        verbose_name = '考核'
        verbose_name_plural = '考核'
        ordering = ['-assessment_date']

class AssessmentItem(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='items', verbose_name='所属考核')
    name = models.CharField(max_length=100, verbose_name='考核项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='最高分值')
    order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.assessment.name} - {self.name}'

    class Meta:
        db_table = 'assessment_item'
        verbose_name = '考核项目'
        verbose_name_plural = '考核项目'
        ordering = ['assessment', 'order']

class AssessmentScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scores', verbose_name='考核')
    assessment_item = models.ForeignKey(AssessmentItem, on_delete=models.CASCADE, related_name='scores', verbose_name='考核项目')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='assessment_scores', verbose_name='队员')
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='得分')
    notes = models.TextField(blank=True, verbose_name='评分备注')
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='记录人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.player.name} - {self.assessment_item.name} - {self.score}'

    class Meta:
        db_table = 'assessment_score'
        verbose_name = '考核成绩'
        verbose_name_plural = '考核成绩'
        ordering = ['assessment', 'player', 'assessment_item']
        unique_together = ['assessment', 'assessment_item', 'player']

# 成就管理模块 - 优化版
class AchievementCategory(models.Model):
    """成就类别"""
    name = models.CharField(max_length=50, verbose_name='类别名称')
    description = models.TextField(blank=True, null=True, verbose_name='类别描述')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='图标')
    color = models.CharField(max_length=20, default='#1890ff', verbose_name='颜色')
    cover_image = models.URLField(blank=True, null=True, verbose_name='封面图片')
    order = models.IntegerField(default=0, verbose_name='显示顺序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 添加新字段
    display_style = models.CharField(max_length=20, default='grid', choices=[
        ('grid', '网格'),
        ('list', '列表'),
        ('showcase', '展示柜'),
    ], verbose_name='显示样式')
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, 
                                       related_name='subcategories', verbose_name='父类别')
    
    class Meta:
        db_table = 'achievement_category'
        verbose_name = '成就类别'
        verbose_name_plural = '成就类别'
        ordering = ['order', 'name']
        
    def __str__(self):
        return self.name
    
    def get_achievement_count(self):
        """获取该类别下的成就数量"""
        return self.personal_achievements.count()
    
    def get_unlocked_count(self, player):
        """获取某队员在该类别下已解锁的成就数量"""
        return PlayerAchievement.objects.filter(
            player=player, 
            achievement__category=self
        ).count()

class AchievementSeries(models.Model):
    """成就系列 - 将相关成就组织成系列"""
    name = models.CharField(max_length=50, verbose_name='系列名称')
    description = models.TextField(blank=True, verbose_name='系列描述')
    category = models.ForeignKey(AchievementCategory, on_delete=models.CASCADE, 
                               related_name='series', verbose_name='所属类别')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='图标')
    cover_image = models.URLField(blank=True, null=True, verbose_name='封面图片')
    order = models.IntegerField(default=0, verbose_name='显示顺序')
    is_sequential = models.BooleanField(default=False, verbose_name='是否按顺序解锁')
    bonus_points = models.PositiveIntegerField(default=0, verbose_name='系列完成额外积分')
    
    class Meta:
        db_table = 'achievement_series'
        verbose_name = '成就系列'
        verbose_name_plural = '成就系列'
        ordering = ['category', 'order', 'name']
        
    def __str__(self):
        return self.name

class PersonalAchievement(models.Model):
    """个人成就定义"""
    AWARD_METHOD_CHOICES = (
        ('manual', '手动颁发'),
        ('auto_task', '自动(任务)'),
        ('auto_assessment', '自动(考核)'),
    )
    
    DIFFICULTY_CHOICES = (
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
        ('expert', '专家'),
        ('master', '大师'),
    )
    
    RARITY_CHOICES = (
        ('common', '普通'),
        ('uncommon', '不常见'),
        ('rare', '稀有'),
        ('epic', '史诗'),
        ('legendary', '传奇'),
    )
    
    name = models.CharField(max_length=100, verbose_name='成就名称')
    description = models.TextField(blank=True, verbose_name='成就描述')
    category = models.ForeignKey(AchievementCategory, on_delete=models.PROTECT, related_name='personal_achievements', verbose_name='所属类别')
    points = models.PositiveIntegerField(default=0, verbose_name='积分')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='图标')
    
    # 徽章字段增强
    badge_image_locked = models.URLField(blank=True, null=True, verbose_name='未解锁徽章图片')
    badge_image = models.URLField(blank=True, null=True, verbose_name='徽章图片')
    badge_animation = models.URLField(blank=True, null=True, verbose_name='徽章解锁动画')
    
    # 成就特性
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name='难度')
    rarity = models.CharField(max_length=10, choices=RARITY_CHOICES, default='common', verbose_name='稀有度')
    hidden = models.BooleanField(default=False, verbose_name='是否隐藏成就')
    featured = models.BooleanField(default=False, verbose_name='是否精选成就')
    
    # 解锁条件
    criteria_type = models.CharField(max_length=20, choices=AWARD_METHOD_CHOICES, default='manual', verbose_name='颁发方式')
    criteria_value = models.CharField(max_length=255, blank=True, null=True, verbose_name='条件值')
    criteria_description = models.CharField(max_length=255, blank=True, null=True, verbose_name='条件描述')
    
    # 额外信息
    unlock_message = models.TextField(blank=True, null=True, verbose_name='解锁提示信息')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 添加新字段
    series = models.ForeignKey(AchievementSeries, null=True, blank=True, on_delete=models.SET_NULL, 
                             related_name='achievements', verbose_name='所属系列')
    tier = models.IntegerField(default=1, verbose_name='阶段/等级')
    sequence = models.IntegerField(default=0, verbose_name='序列顺序')
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, 
                                         related_name='unlocks', verbose_name='前置成就')
    
    class Meta:
        db_table = 'personal_achievement'
        verbose_name = '个人成就'
        verbose_name_plural = '个人成就'
        ordering = ['category', 'difficulty', '-rarity', 'name']
        
    def __str__(self):
        return self.name
    
    def get_unlock_count(self):
        """获取解锁该成就的队员数量"""
        return self.player_records.count()
    
    def get_unlock_rate(self):
        """获取成就解锁率"""
        total_players = Player.objects.count()
        if total_players == 0:
            return 0
        unlocked = self.get_unlock_count()
        return round((unlocked / total_players) * 100, 1)
    
    def get_criteria_display(self):
        """获取人类可读的解锁条件描述"""
        if self.criteria_description:
            return self.criteria_description
            
        if self.criteria_type == 'manual':
            return '由教练手动颁发'
            
        try:
            if self.criteria_type == 'auto_task':
                criteria = json.loads(self.criteria_value)
                task_type = criteria.get('type')
                
                if task_type == 'completion_count':
                    return f"完成{criteria.get('count', 0)}个任务"
                elif task_type == 'consecutive_days':
                    return f"连续{criteria.get('consecutive_days', 0)}天完成任务"
                    
            elif self.criteria_type == 'auto_assessment':
                criteria = json.loads(self.criteria_value)
                return f"考核得分达到{criteria.get('min_score', 0)}分"
                
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
            
        return '完成特定条件'

class PlayerAchievement(models.Model):
    """队员获得的成就记录"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='achievements', verbose_name='队员')
    achievement = models.ForeignKey(PersonalAchievement, on_delete=models.CASCADE, related_name='player_records', verbose_name='成就')
    awarded_date = models.DateField(default=date.today, verbose_name='获得日期')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='颁发人')
    notes = models.TextField(blank=True, verbose_name='颁发备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    # 新增字段
    progress = models.IntegerField(default=100, verbose_name='完成进度') # 100表示完全解锁
    shared = models.BooleanField(default=False, verbose_name='是否已分享')
    
    class Meta:
        db_table = 'player_achievement'
        verbose_name = '队员成就记录'
        verbose_name_plural = '队员成就记录'
        ordering = ['-awarded_date']
        unique_together = ['player', 'achievement'] # 一个队员只能获得同一个成就一次
        
    def __str__(self):
        return f"{self.player.name} - {self.achievement.name}"
        
    def share_achievement(self):
        """分享成就"""
        self.shared = True
        self.save()
        return True

class TeamAchievement(models.Model):
    """队伍成就"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements', verbose_name='队伍')
    name = models.CharField(max_length=100, verbose_name='成就名称')
    description = models.TextField(blank=True, verbose_name='成就描述')
    category = models.ForeignKey(AchievementCategory, on_delete=models.PROTECT, related_name='team_achievements', verbose_name='所属类别')
    points = models.PositiveIntegerField(default=0, verbose_name='积分')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='图标')
    badge_image = models.URLField(blank=True, null=True, verbose_name='徽章图片')
    awarded_date = models.DateField(default=date.today, verbose_name='获得日期')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='颁发人')
    notes = models.TextField(blank=True, verbose_name='颁发备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'team_achievement'
        verbose_name = '队伍成就'
        verbose_name_plural = '队伍成就'
        ordering = ['-awarded_date']
        
    def __str__(self):
        return f"{self.team.name} - {self.name}"
