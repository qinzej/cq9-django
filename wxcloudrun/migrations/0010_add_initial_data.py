from django.db import migrations

def create_initial_data(apps, schema_editor):
    School = apps.get_model('wxcloudrun', 'School')
    EnrollmentYear = apps.get_model('wxcloudrun', 'EnrollmentYear')

    # 创建学校数据
    schools = [
        {'name': '泡小天府'},
        {'name': '省教科院'}
    ]
    for school_data in schools:
        School.objects.create(**school_data)

    # 创建入学年份数据
    years = range(2020, 2027)
    for year in years:
        EnrollmentYear.objects.create(year=year)

def reverse_initial_data(apps, schema_editor):
    School = apps.get_model('wxcloudrun', 'School')
    EnrollmentYear = apps.get_model('wxcloudrun', 'EnrollmentYear')
    Player = apps.get_model('wxcloudrun', 'Player')
    
    # 先将所有Player的school设置为null
    Player.objects.filter(school__name__in=['泡小天府', '省教科院']).update(school=None)
    
    # 删除学校数据
    School.objects.filter(name__in=['泡小天府', '省教科院']).delete()
    
    # 删除入学年份数据
    EnrollmentYear.objects.filter(year__in=range(2020, 2027)).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('wxcloudrun', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]