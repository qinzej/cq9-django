# Generated by Django 3.2.8 on 2025-03-08 22:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0021_achievement_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='task_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='wxcloudrun.tasktype', verbose_name='任务类型'),
        ),
    ]
