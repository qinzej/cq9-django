from datetime import datetime, date
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone

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
        current_year = datetime.now().year
        years_since_enrollment = current_year - self.enrollment_year.year
        return years_since_enrollment + 1

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
    FREQUENCY_CHOICES = [
        ('once', '一次性'),
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]
    
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('completed', '已结束'),
        ('expired', '已过期'),
        ('draft', '草稿'),
    ]
    
    title = models.CharField(max_length=100, verbose_name='任务标题')
    description = models.TextField(verbose_name='任务描述')
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='created_tasks', verbose_name='创建教练')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_tasks', verbose_name='所属队伍')
    task_type = models.ForeignKey(TaskType, on_delete=models.SET_NULL, null=True, verbose_name='任务类型')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='once', verbose_name='频率')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    points = models.IntegerField(default=1, verbose_name='积分值')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='状态')
    require_proof = models.BooleanField(default=False, verbose_name='是否需要证明')
    has_reminder = models.BooleanField(default=False, verbose_name='是否有提醒')
    reminder_time = models.TimeField(null=True, blank=True, verbose_name='提醒时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        
    def __str__(self):
        return self.title
    
    def get_completion_rate(self):
        """获取任务完成率"""
        team_players = self.team.players.count()
        if team_players == 0:
            return 0
            
        # 获取当天或总体的完成人数
        if self.frequency == 'once':
            completed = self.completions.filter(status='completed').values('player').distinct().count()
        else:
            # 对于周期性任务，计算当天的完成率
            today = date.today()
            completed = self.completions.filter(
                completion_date=today,
                status='completed'
            ).count()
            
        return round((completed / team_players) * 100)
        
    def get_task_streak(self, player):
        """获取指定队员的连续完成天数"""
        if self.frequency == 'once':
            # 一次性任务没有连续概念
            completion = self.completions.filter(player=player, status='completed').first()
            return 1 if completion else 0
            
        # 查询队员最近的完成记录，按日期倒序排列
        completions = self.completions.filter(
            player=player,
            status='completed'
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
            
            if self.frequency == 'daily' and date_diff == 1:
                streak += 1
            elif self.frequency == 'weekly' and date_diff <= 7 and current_date.weekday() == last_date.weekday():
                streak += 1
            elif self.frequency == 'monthly' and current_date.month == (last_date.month - 1) % 12:
                streak += 1
            else:
                break
                
            last_date = current_date
            
        return streak

class TaskCompletion(models.Model):
    """任务完成记录"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('completed', '已完成'),
        ('rejected', '已驳回'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completions', verbose_name='关联任务')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='task_completions', verbose_name='完成队员')
    completion_date = models.DateField(default=date.today, verbose_name='完成日期')
    completion_time = models.TimeField(auto_now_add=True, verbose_name='完成时间')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='completed', verbose_name='状态')
    comment = models.TextField(blank=True, null=True, verbose_name='备注')
    attachment = models.URLField(blank=True, null=True, verbose_name='附件链接')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '任务完成记录'
        verbose_name_plural = '任务完成记录'
        db_table = 'task_completion'
        ordering = ['-completion_date', '-completion_time']
    
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
