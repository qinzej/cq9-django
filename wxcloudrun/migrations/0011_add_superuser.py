from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # 创建超级管理员账号
    superuser = User.objects.create(
        username='lihai',
        password=make_password('Lihai#87'),
        is_staff=True,
        is_active=True,
        is_superuser=True
    )

def reverse_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    # 删除超级管理员账号
    User.objects.filter(username='lihai').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('wxcloudrun', '0010_add_initial_data'),
    ]

    operations = [
        migrations.RunPython(create_superuser, reverse_superuser),
    ]