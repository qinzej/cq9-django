from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def create_coach_group(apps, schema_editor):
    # 创建教练组
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Team = apps.get_model('wxcloudrun', 'Team')
    Player = apps.get_model('wxcloudrun', 'Player')
    Parent = apps.get_model('wxcloudrun', 'Parent')
    
    coach_group, created = Group.objects.get_or_create(name='教练')
    
    # 获取相关模型的ContentType
    team_ct = ContentType.objects.get_for_model(Team)
    player_ct = ContentType.objects.get_for_model(Player)
    parent_ct = ContentType.objects.get_for_model(Parent)
    
    # 定义教练组的权限
    permissions = [
        # 队伍权限
        Permission.objects.get(content_type=team_ct, codename='view_team'),
        Permission.objects.get(content_type=team_ct, codename='change_team'),
        
        # 队员权限
        Permission.objects.get(content_type=player_ct, codename='view_player'),
        Permission.objects.get(content_type=player_ct, codename='add_player'),
        Permission.objects.get(content_type=player_ct, codename='change_player'),
        
        # 家长权限
        Permission.objects.get(content_type=parent_ct, codename='view_parent'),
        Permission.objects.get(content_type=parent_ct, codename='add_parent'),
        Permission.objects.get(content_type=parent_ct, codename='change_parent'),
    ]
    
    # 为教练组分配权限
    coach_group.permissions.set(permissions)

def remove_coach_group(apps, schema_editor):
    # 删除教练组
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='教练').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('wxcloudrun', '0012_auto_20250303_1648'),  # 修正为正确的迁移文件
    ]
    
    operations = [
        migrations.RunPython(create_coach_group, remove_coach_group),
    ]