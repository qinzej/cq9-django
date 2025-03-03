from datetime import datetime
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
class Task(models.Model):
    PERIOD_CHOICES = (
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('once', '一次性'),
    )
    title = models.CharField(max_length=200, verbose_name='任务标题')
    description = models.TextField(verbose_name='任务描述')
    teams = models.ManyToManyField(Team, related_name='tasks', verbose_name='分配队伍')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='once', verbose_name='任务周期')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'task'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']

# 任务完成记录
class TaskCompletion(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completions', verbose_name='任务')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='task_completions', verbose_name='队员')
    completion_date = models.DateField(verbose_name='完成日期')
    proof = models.ImageField(upload_to='task_proofs/', blank=True, null=True, verbose_name='完成证明')
    notes = models.TextField(blank=True, verbose_name='备注')
    verified = models.BooleanField(default=False, verbose_name='是否已验证')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_tasks', verbose_name='验证人')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.player.name} - {self.task.title} - {self.completion_date}'

    class Meta:
        db_table = 'task_completion'
        verbose_name = '任务完成记录'
        verbose_name_plural = '任务完成记录'
        ordering = ['-completion_date']
        unique_together = ['task', 'player', 'completion_date']

# 成就管理模块
class AchievementLevel(models.Model):
    name = models.CharField(max_length=50, verbose_name='等级名称')
    description = models.TextField(blank=True, verbose_name='等级描述')
    order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'achievement_level'
        verbose_name = '成就等级'
        verbose_name_plural = '成就等级'
        ordering = ['order']

class PersonalAchievement(models.Model):
    ACHIEVEMENT_TYPE_CHOICES = (
        ('manual', '手动发放'),
        ('task', '任务完成'),
        ('assessment', '考核成绩'),
    )
    name = models.CharField(max_length=100, verbose_name='成就名称')
    description = models.TextField(blank=True, verbose_name='成就描述')
    level = models.ForeignKey(AchievementLevel, on_delete=models.PROTECT, verbose_name='成就等级')
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES, default='manual', verbose_name='获取方式')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联任务')
    task_count = models.IntegerField(default=0, verbose_name='任务完成次数要求')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'personal_achievement'
        verbose_name = '个人成就'
        verbose_name_plural = '个人成就'

class PlayerAchievement(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='achievements', verbose_name='队员')
    achievement = models.ForeignKey(PersonalAchievement, on_delete=models.CASCADE, verbose_name='成就')
    awarded_date = models.DateField(verbose_name='获得日期')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='颁发人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.player.name} - {self.achievement.name}'

    class Meta:
        db_table = 'player_achievement'
        verbose_name = '队员成就记录'
        verbose_name_plural = '队员成就记录'
        ordering = ['-awarded_date']
        unique_together = ['player', 'achievement']

class TeamAchievement(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements', verbose_name='队伍')
    name = models.CharField(max_length=100, verbose_name='成就名称')
    description = models.TextField(blank=True, verbose_name='成就描述')
    competition_name = models.CharField(max_length=200, blank=True, verbose_name='比赛名称')
    awarded_date = models.DateField(verbose_name='获得日期')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='颁发人')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.team.name} - {self.name}'

    class Meta:
        db_table = 'team_achievement'
        verbose_name = '队伍成就'
        verbose_name_plural = '队伍成就'
        ordering = ['-awarded_date']

# 考核管理模块
class Assessment(models.Model):
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
