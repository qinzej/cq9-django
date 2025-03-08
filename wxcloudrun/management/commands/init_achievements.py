import os
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from wxcloudrun.models import (
    AchievementCategory, AchievementSeries, PersonalAchievement
)
from django.conf import settings
from wxcloudrun.utils.cloud_storage import CloudStorage

class Command(BaseCommand):
    help = '初始化青少年棒球俱乐部成就系统的示例数据'

    def handle(self, *args, **options):
        try:
            # 使用事务确保数据一致性
            with transaction.atomic():
                self.stdout.write('开始初始化成就系统...')
                
                # 创建成就类别
                self.create_categories()
                
                # 创建成就系列
                self.create_series()
                
                # 创建个人成就
                self.create_achievements()
                
                self.stdout.write(self.style.SUCCESS('成就系统初始化完成！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'初始化失败：{str(e)}'))
    
    def create_categories(self):
        """创建成就类别"""
        self.stdout.write('创建成就类别...')
        
        # 删除已有类别
        AchievementCategory.objects.all().delete()
        
        # 创建新类别
        categories = [
            {
                'name': '基础技能',
                'description': '棒球基本技能的掌握程度',
                'icon': '⚾',
                'color': '#1890ff', 
                'display_style': 'grid'
            },
            {
                'name': '比赛成就',
                'description': '在正式比赛中的表现与成绩',
                'icon': '🏆',
                'color': '#52c41a',
                'display_style': 'showcase'
            },
            {
                'name': '团队精神',
                'description': '展现团队合作与领导能力',
                'icon': '👥',
                'color': '#722ed1',
                'display_style': 'grid'
            },
            {
                'name': '进阶技巧',
                'description': '高级棒球技巧的掌握',
                'icon': '🔥',
                'color': '#fa8c16',
                'display_style': 'list'
            },
            {
                'name': '特殊成就',
                'description': '特殊目标与里程碑',
                'icon': '⭐',
                'color': '#eb2f96',
                'display_style': 'grid'
            }
        ]
        
        for cat_data in categories:
            # 上传示例封面图片
            sample_image_path = os.path.join(settings.BASE_DIR, 'static', 'sample_images', f"category_{cat_data['name']}.png")
            if os.path.exists(sample_image_path):
                with open(sample_image_path, 'rb') as img_file:
                    cover_url = CloudStorage.upload_file(img_file, folder=f"categories/{cat_data['name'].lower()}")
                    if cover_url:
                        cat_data['cover_image'] = cover_url
            
            AchievementCategory.objects.create(**cat_data)
            self.stdout.write(f"  - 已创建类别：{cat_data['name']}")
    
    def create_series(self):
        """创建成就系列"""
        self.stdout.write('创建成就系列...')
        
        # 删除已有系列
        AchievementSeries.objects.all().delete()
        
        # 获取已创建的类别
        categories = {cat.name: cat for cat in AchievementCategory.objects.all()}
        
        # 创建成就系列
        series_data = [
            # 基础技能系列
            {
                'name': '打击系列',
                'description': '从初学者到熟练打击手的进阶之路',
                'category': categories['基础技能'],
                'icon': '🏏',
                'is_sequential': True,
                'bonus_points': 50
            },
            {
                'name': '投球系列',
                'description': '掌握各种投球技巧',
                'category': categories['基础技能'],
                'icon': '🎯',
                'is_sequential': True,
                'bonus_points': 50
            },
            {
                'name': '防守系列',
                'description': '成为防守高手的必经之路',
                'category': categories['基础技能'],
                'icon': '🧤',
                'is_sequential': True,
                'bonus_points': 50
            },
            
            # 比赛成就系列
            {
                'name': '首发阵容',
                'description': '成为首发球员的荣誉记录',
                'category': categories['比赛成就'],
                'icon': '1️⃣',
                'is_sequential': False,
                'bonus_points': 100
            },
            {
                'name': '关键时刻',
                'description': '在比赛关键时刻的精彩表现',
                'category': categories['比赛成就'],
                'icon': '⏱️',
                'is_sequential': False,
                'bonus_points': 80
            },
            
            # 团队精神系列
            {
                'name': '团队合作',
                'description': '展现良好的团队合作精神',
                'category': categories['团队精神'],
                'icon': '🤝',
                'is_sequential': False,
                'bonus_points': 30
            },
            {
                'name': '领导力',
                'description': '在团队中发挥领导作用',
                'category': categories['团队精神'],
                'icon': '👑',
                'is_sequential': True,
                'bonus_points': 60
            }
        ]
        
        for series_item in series_data:
            # 上传示例封面图片
            sample_image_path = os.path.join(settings.BASE_DIR, 'static', 'sample_images', f"series_{series_item['name']}.png")
            if os.path.exists(sample_image_path):
                with open(sample_image_path, 'rb') as img_file:
                    cover_url = CloudStorage.upload_file(img_file, folder=f"series/{series_item['name'].lower()}")
                    if cover_url:
                        series_item['cover_image'] = cover_url
            
            AchievementSeries.objects.create(**series_item)
            self.stdout.write(f"  - 已创建系列：{series_item['name']} (归属：{series_item['category'].name})")
    
    def create_achievements(self):
        """创建个人成就"""
        self.stdout.write('创建个人成就...')
        
        # 删除已有成就
        PersonalAchievement.objects.all().delete()
        
        # 获取所有系列
        series = {s.name: s for s in AchievementSeries.objects.all()}
        categories = {cat.name: cat for cat in AchievementCategory.objects.all()}
        
        # 创建成就列表
        achievements_data = [
            # 打击系列成就
            {
                'name': '初级击球手',
                'description': '完成基本击球训练',
                'category': categories['基础技能'],
                'series': series['打击系列'],
                'points': 10,
                'icon': '🏏',
                'difficulty': 'easy',
                'rarity': 'common',
                'tier': 1,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 5}),
                'criteria_description': '完成5次击球练习任务',
            },
            {
                'name': '中级击球手',
                'description': '展示稳定的击球能力',
                'category': categories['基础技能'],
                'series': series['打击系列'],
                'points': 30,
                'icon': '🏏',
                'difficulty': 'medium',
                'rarity': 'uncommon',
                'tier': 2,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 15}),
                'criteria_description': '完成15次击球练习任务',
            },
            {
                'name': '高级击球手',
                'description': '精通各种击球技巧',
                'category': categories['基础技能'],
                'series': series['打击系列'],
                'points': 50,
                'icon': '🏏',
                'difficulty': 'hard',
                'rarity': 'rare',
                'tier': 3,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 30}),
                'criteria_description': '完成30次击球练习任务',
            },
            
            # 投球系列成就
            {
                'name': '初级投手',
                'description': '学会基本投球姿势',
                'category': categories['基础技能'],
                'series': series['投球系列'],
                'points': 10,
                'icon': '🎯',
                'difficulty': 'easy',
                'rarity': 'common',
                'tier': 1,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 5}),
                'criteria_description': '完成5次投球练习任务',
            },
            {
                'name': '中级投手',
                'description': '掌握变速球技巧',
                'category': categories['基础技能'],
                'series': series['投球系列'],
                'points': 30,
                'icon': '🎯',
                'difficulty': 'medium',
                'rarity': 'uncommon',
                'tier': 2,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 15}),
                'criteria_description': '完成15次投球练习任务',
            },
            
            # 防守系列成就
            {
                'name': '初级守备员',
                'description': '学会基本防守姿势',
                'category': categories['基础技能'],
                'series': series['防守系列'],
                'points': 10,
                'icon': '🧤',
                'difficulty': 'easy',
                'rarity': 'common',
                'tier': 1,
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'completion_count', 'count': 5}),
                'criteria_description': '完成5次防守练习任务',
            },
            
            # 比赛成就
            {
                'name': '首次上场',
                'description': '第一次参加正式比赛',
                'category': categories['比赛成就'],
                'points': 20,
                'icon': '🏟️',
                'difficulty': 'easy',
                'rarity': 'common',
                'criteria_type': 'manual',
                'criteria_description': '首次参加正式比赛',
            },
            {
                'name': '首发球员',
                'description': '成为球队的首发球员',
                'category': categories['比赛成就'],
                'series': series['首发阵容'],
                'points': 50,
                'icon': '1️⃣',
                'difficulty': 'medium',
                'rarity': 'uncommon',
                'criteria_type': 'manual',
                'criteria_description': '在正式比赛中担任首发球员',
            },
            
            # 团队精神成就
            {
                'name': '团队玩家',
                'description': '展示出色的团队合作能力',
                'category': categories['团队精神'],
                'series': series['团队合作'],
                'points': 15,
                'icon': '🤝',
                'difficulty': 'easy',
                'rarity': 'common',
                'criteria_type': 'manual',
                'criteria_description': '通过教练评估的团队合作能力',
            },
            {
                'name': '队长之星',
                'description': '展示出色的领导才能',
                'category': categories['团队精神'],
                'series': series['领导力'],
                'points': 40,
                'icon': '👑',
                'difficulty': 'hard',
                'rarity': 'rare',
                'criteria_type': 'manual',
                'criteria_description': '被任命为球队队长或副队长',
            },
            
            # 特殊成就
            {
                'name': '全勤王',
                'description': '连续30天参加训练',
                'category': categories['特殊成就'],
                'points': 60,
                'icon': '📅',
                'difficulty': 'medium',
                'rarity': 'rare',
                'criteria_type': 'auto_task',
                'criteria_value': json.dumps({'type': 'consecutive_days', 'consecutive_days': 30}),
                'criteria_description': '连续30天完成训练任务',
                'featured': True
            },
            {
                'name': '小有名气',
                'description': '在媒体或比赛中获得表彰',
                'category': categories['特殊成就'],
                'points': 100,
                'icon': '📰',
                'difficulty': 'expert',
                'rarity': 'epic',
                'criteria_type': 'manual',
                'criteria_description': '在媒体报道或赛事获得特别表彰',
                'hidden': True
            },
        ]
        
        # 为成就创建前置条件
        prerequisites = {
            '中级击球手': ['初级击球手'],
            '高级击球手': ['中级击球手'],
            '中级投手': ['初级投手'],
            '队长之星': ['团队玩家'],
        }
        
        # 创建成就并记录ID以便后续设置前置条件
        created_achievements = {}
        
        for ach_data in achievements_data:
            # 上传徽章图片
            for image_type in ['badge_image_locked', 'badge_image']:
                sample_image_path = os.path.join(
                    settings.BASE_DIR, 'static', 'sample_images', 
                    f"{image_type}_{ach_data['name']}.png"
                )
                if os.path.exists(sample_image_path):
                    with open(sample_image_path, 'rb') as img_file:
                        badge_url = CloudStorage.upload_file(
                            img_file, 
                            folder=f"badges/{ach_data['name'].lower()}"
                        )
                        if badge_url:
                            ach_data[image_type] = badge_url
            
            # 创建成就
            achievement = PersonalAchievement.objects.create(**ach_data)
            created_achievements[achievement.name] = achievement
            self.stdout.write(f"  - 已创建成就：{achievement.name} ({achievement.difficulty})")
        
        # 设置前置成就
        for ach_name, prereq_names in prerequisites.items():
            if ach_name in created_achievements:
                achievement = created_achievements[ach_name]
                for prereq_name in prereq_names:
                    if prereq_name in created_achievements:
                        achievement.prerequisites.add(created_achievements[prereq_name])
                achievement.save()
                self.stdout.write(f"  - 已设置成就 {ach_name} 的前置条件")
