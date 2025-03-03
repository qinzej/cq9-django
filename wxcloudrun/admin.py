from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
import pandas as pd
from .models import Coach, Parent, Player, School, EnrollmentYear, Team, Task, TaskCompletion, AchievementLevel, PersonalAchievement, PlayerAchievement, TeamAchievement, Assessment, AssessmentItem, AssessmentScore, TeamResult

# 设置管理后台标题
admin.site.site_header = '超群九人后台管理'
admin.site.site_title = '超群九人后台管理'
admin.site.index_title = '超群九人后台管理'

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(EnrollmentYear)
class EnrollmentYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'created_at', 'updated_at']
    ordering = ['-year']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# 设置应用分组
admin.site.index_template = 'admin/custom_index.html'

# 定义应用分组
class CoachingAdminArea(admin.AdminSite):
    site_header = '教练管理'

coaching_admin_site = CoachingAdminArea(name='coaching')

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'speciality', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'phone', 'speciality']
    raw_id_fields = ['user']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_delete_permission(request, obj)

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'get_players', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'phone']
    filter_horizontal = ['players']

    def get_players(self, obj):
        return ', '.join([player.name for player in obj.players.all()])
    get_players.short_description = '关联队员'

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'enrollment_year', 'grade', 'get_parents']
    list_filter = ['school', 'enrollment_year']
    search_fields = ['name', 'school']
    filter_horizontal = ['parents']
    fields = ['name', 'school', 'enrollment_year', 'notes', 'parents']
    change_list_template = 'admin/player_changelist.html'

    def get_parents(self, obj):
        return ', '.join([parent.name for parent in obj.parents.all()])
    get_parents.short_description = '家长'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.import_excel, name='player_import_excel'),
        ]
        return custom_urls + urls

    def import_excel(self, request):
        if request.method == 'POST':
            if 'excel_file' not in request.FILES:
                self.message_user(request, '请选择Excel文件', level=messages.ERROR)
                return redirect('..')
            
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                required_columns = ['队员姓名', '学校', '入学年份', '家长姓名', '家长电话']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f'Excel文件缺少必要的列：{col}')

                for _, row in df.iterrows():
                    # 获取或创建学校
                    school = None
                    if pd.notna(row['学校']):
                        school = School.objects.filter(name=row['学校']).first()
                        if not school:
                            self.message_user(request, f'学校 "{row["学校"]}" 不存在，请先在系统中添加该学校', level=messages.ERROR)
                            return redirect('..')

                    # 获取入学年份
                    enrollment_year = None
                    if pd.notna(row['入学年份']):
                        try:
                            year = int(row['入学年份'])
                            enrollment_year = EnrollmentYear.objects.filter(year=year).first()
                            if not enrollment_year:
                                self.message_user(request, f'入学年份 {year} 不存在，请先在系统中添加该年份', level=messages.ERROR)
                                return redirect('..')
                        except (ValueError, TypeError):
                            self.message_user(request, f'入学年份格式不正确：{row["入学年份"]}', level=messages.ERROR)
                            return redirect('..')

                    # 创建或更新家长信息
                    parent = None
                    if pd.notna(row['家长电话']):
                        parent, _ = Parent.objects.get_or_create(
                            phone=str(row['家长电话']),
                            defaults={
                                'name': row['家长姓名'] if pd.notna(row['家长姓名']) else ''
                            }
                        )
                    
                    # 创建队员记录
                    player = Player.objects.create(
                        name=row['队员姓名'],
                        school=school,
                        enrollment_year=enrollment_year,
                        notes=row['备注'] if pd.notna(row.get('备注')) else ''
                    )
                    
                    # 如果有家长信息，建立关联
                    if parent:
                        player.parents.add(parent)
                
                self.message_user(request, '导入成功')
                return redirect('..')
            except Exception as e:
                self.message_user(request, f'导入失败：{str(e)}', level=messages.ERROR)
                return redirect('..')
        
        return render(request, 'admin/player_import.html')

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# 取消注册默认的User和Group管理
admin.site.unregister(User)
admin.site.unregister(Group)

# 重新注册User管理
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_superuser', 'get_groups']
    list_filter = ['is_staff', 'is_superuser', 'groups']
    
    def get_groups(self, obj):
        return ', '.join([g.name for g in obj.groups.all()])
    get_groups.short_description = '角色'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(id=request.user.id)
        return qs

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return (
                (None, {'fields': ('username', 'password1', 'password2')}),
                ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
                ('权限', {
                    'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
                    'description': '选择用户角色：<br/>- 超级管理员：选中"超级用户"<br/>- 教练：选择"教练"组'
                })
            )
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 检查用户是否属于教练组
        coach_group = Group.objects.get(name='教练')
        if coach_group in obj.groups.all():
            # 如果用户是教练，确保存在对应的Coach记录
            Coach.objects.get_or_create(
                user=obj,
                defaults={
                    'phone': '',
                    'speciality': '',
                    'introduction': '',
                    'is_active': True
                }
            )
        else:
            # 如果用户不是教练，删除对应的Coach记录（如果存在）
            Coach.objects.filter(user=obj).delete()

# 重新注册Group管理，只允许超级管理员访问
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'head_coach', 'get_coaches', 'get_players', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name']
    filter_horizontal = ['coaches', 'players']

    def get_coaches(self, obj):
        return ', '.join([coach.user.username for coach in obj.coaches.all()])
    get_coaches.short_description = '教练'

    def get_players(self, obj):
        return ', '.join([player.name for player in obj.players.all()])
    get_players.short_description = '队员'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(models.Q(head_coach__user=request.user) | models.Q(coaches__user=request.user))
        return qs

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.head_coach.user == request.user or obj.coaches.filter(user=request.user).exists()
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.head_coach.user == request.user
        return request.user.is_superuser

@admin.register(TeamResult)
class TeamResultAdmin(admin.ModelAdmin):
    list_display = ['team', 'competition_name', 'competition_date', 'result']
    list_filter = ['competition_date', 'team']
    search_fields = ['competition_name', 'team__name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'period', 'start_date', 'end_date', 'created_by']
    list_filter = ['period', 'start_date', 'created_by']
    search_fields = ['title', 'description']
    filter_horizontal = ['teams']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.created_by == request.user
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ['task', 'player', 'completion_date', 'verified', 'verified_by']
    list_filter = ['completion_date', 'verified', 'task']
    search_fields = ['task__title', 'player__name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AchievementLevel)
class AchievementLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering = ['order']
    search_fields = ['name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(PersonalAchievement)
class PersonalAchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'achievement_type']
    list_filter = ['level', 'achievement_type']
    search_fields = ['name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ['player', 'achievement', 'awarded_date', 'awarded_by']
    list_filter = ['awarded_date', 'achievement']
    search_fields = ['player__name', 'achievement__name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(TeamAchievement)
class TeamAchievementAdmin(admin.ModelAdmin):
    list_display = ['team', 'name', 'competition_name', 'awarded_date', 'awarded_by']
    list_filter = ['awarded_date', 'team']
    search_fields = ['name', 'team__name', 'competition_name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'assessment_date', 'created_by']
    list_filter = ['assessment_date', 'created_by']
    search_fields = ['name']
    filter_horizontal = ['teams']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.created_by == request.user
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AssessmentItem)
class AssessmentItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'assessment', 'max_score', 'order']
    list_filter = ['assessment']
    search_fields = ['name', 'assessment__name']
    ordering = ['assessment', 'order']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AssessmentScore)
class AssessmentScoreAdmin(admin.ModelAdmin):
    list_display = ['assessment', 'assessment_item', 'player', 'score', 'recorded_by']
    list_filter = ['assessment', 'assessment_item', 'recorded_by']
    search_fields = ['player__name', 'assessment__name']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            return obj.recorded_by == request.user
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser