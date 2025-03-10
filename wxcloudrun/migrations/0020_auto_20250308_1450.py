# Generated by Django 3.2.8 on 2025-03-08 14:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wxcloudrun', '0019_achievementcategory_personalachievement_playerachievement_teamachievement'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievementcategory',
            name='display_style',
            field=models.CharField(choices=[('grid', '网格'), ('list', '列表'), ('showcase', '展示柜')], default='grid', max_length=20, verbose_name='显示样式'),
        ),
        migrations.AddField(
            model_name='achievementcategory',
            name='parent_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategories', to='wxcloudrun.achievementcategory', verbose_name='父类别'),
        ),
        migrations.AddField(
            model_name='personalachievement',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, related_name='unlocks', to='wxcloudrun.PersonalAchievement', verbose_name='前置成就'),
        ),
        migrations.AddField(
            model_name='personalachievement',
            name='sequence',
            field=models.IntegerField(default=0, verbose_name='序列顺序'),
        ),
        migrations.AddField(
            model_name='personalachievement',
            name='tier',
            field=models.IntegerField(default=1, verbose_name='阶段/等级'),
        ),
        migrations.CreateModel(
            name='AchievementSeries',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='系列名称')),
                ('description', models.TextField(blank=True, verbose_name='系列描述')),
                ('icon', models.CharField(blank=True, max_length=50, null=True, verbose_name='图标')),
                ('cover_image', models.URLField(blank=True, null=True, verbose_name='封面图片')),
                ('order', models.IntegerField(default=0, verbose_name='显示顺序')),
                ('is_sequential', models.BooleanField(default=False, verbose_name='是否按顺序解锁')),
                ('bonus_points', models.PositiveIntegerField(default=0, verbose_name='系列完成额外积分')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='series', to='wxcloudrun.achievementcategory', verbose_name='所属类别')),
            ],
            options={
                'verbose_name': '成就系列',
                'verbose_name_plural': '成就系列',
                'db_table': 'achievement_series',
                'ordering': ['category', 'order', 'name'],
            },
        ),
        migrations.AddField(
            model_name='personalachievement',
            name='series',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='achievements', to='wxcloudrun.achievementseries', verbose_name='所属系列'),
        ),
    ]
