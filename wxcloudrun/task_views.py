from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import jwt
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Task, TaskCompletion, Player, Team, Coach
from django.conf import settings
from django.db.models import Count, Q, Subquery, OuterRef, Exists
import logging

# 设置日志
logger = logging.getLogger('log')

def verify_token_and_get_player(request, player_id=None):
    """验证token并获取队员信息"""
    auth_header = request.headers.get('Authorization')
    logger.info(f"Auth header: {auth_header[:20] if auth_header else 'None'}")
    
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f"无效的token格式: {auth_header}")
        return None, JsonResponse({'code': 401, 'message': '无效的token格式'}, status=401)
    
    token = auth_header.split(' ')[1]
    
    try:
        # 使用JWT_SECRET_KEY而非SECRET_KEY
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        logger.info(f"Token decoded for user_id: {payload.get('user_id')}, type: {payload.get('user_type')}")
        
        if payload.get('user_type') != 'parent':
            logger.error(f"用户类型错误: {payload.get('user_type')}")
            return None, JsonResponse({'code': 401, 'message': '用户类型错误'}, status=401)
            
        parent_id = payload.get('user_id')
    except jwt.ExpiredSignatureError:
        logger.error("Token已过期")
        return None, JsonResponse({'code': 401, 'message': 'token已过期'}, status=401)
    except jwt.InvalidTokenError as e:
        logger.error(f"无效的token: {str(e)}")
        return None, JsonResponse({'code': 401, 'message': '无效的token'}, status=401)
    
    # 如果没有提供player_id，返回parent_id
    if not player_id:
        return parent_id, None
    
    # 验证队员是否属于该家长
    try:
        player = Player.objects.get(id=player_id, parents__id=parent_id)
        return player, None
    except Player.DoesNotExist:
        logger.error(f"无权访问队员ID {player_id}")
        return None, JsonResponse({'code': 403, 'message': '无权访问该队员信息'}, status=403)

@csrf_exempt
@require_http_methods(["GET"])
def get_player_tasks(request):
    """获取队员的所有任务"""
    player_id = request.GET.get('player_id')
    
    if not player_id:
        return JsonResponse({'code': 400, 'message': '缺少player_id参数'}, status=400)
    
    # 验证token和获取队员
    player, error_response = verify_token_and_get_player(request, player_id)
    if error_response:
        return error_response
    
    # 获取任务状态筛选
    status_filter = request.GET.get('status')
    
    # 获取队员所在的所有队伍
    teams = player.teams.all()
    
    # 查询这些队伍的所有任务
    tasks = Task.objects.filter(teams__in=teams).distinct()  # 使用distinct避免重复
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    else:
        # 默认只返回活跃任务
        tasks = tasks.filter(status='active')
    
    # 获取当前日期
    today = date.today()
    
    # 准备返回的数据
    tasks_data = []
    for task in tasks:
        # 检查任务是否在有效期内
        is_active = True
        if task.end_date and task.end_date < today:
            is_active = False
        
        # 获取队员今天的完成情况(针对周期性任务)或整体完成情况(一次性任务)
        task_completion = None
        if task.period == 'once':
            task_completion = TaskCompletion.objects.filter(
                task=task, 
                player=player
            ).order_by('-completion_date').first()
        else:
            task_completion = TaskCompletion.objects.filter(
                task=task, 
                player=player, 
                completion_date=today
            ).first()
        
        # 获取团队进度
        team_total = 0
        completed_count = 0
        
        # 获取与当前队员相关的队伍中的情况
        relevant_teams = task.teams.filter(id__in=player.teams.values_list('id', flat=True))
        for team in relevant_teams:
            team_total += team.players.count()
            if task.period == 'once':
                completed_count += TaskCompletion.objects.filter(
                    task=task,
                    verified=True,
                    player__in=team.players.all()
                ).values('player').distinct().count()
            else:
                completed_count += TaskCompletion.objects.filter(
                    task=task,
                    verified=True,
                    completion_date=today,
                    player__in=team.players.all()
                ).values('player').distinct().count()
        
        team_progress = round((completed_count / team_total) * 100) if team_total > 0 else 0
        
        # 获取任务连续完成天数
        streak = task.get_task_streak(player) if is_active else 0
        
        # 组装任务数据
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'period': task.period,
            'start_date': task.start_date.strftime('%Y-%m-%d'),
            'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else None,
            'points': task.points,
            'status': task.status,
            'require_proof': task.require_proof,
            'team_names': [team.name for team in task.teams.all()],
            'task_type': {
                'name': task.task_type.name,
                'icon': task.task_type.icon,
                'color': task.task_type.color
            } if hasattr(task, 'task_type') and task.task_type else None,
            'player_completion': {
                'status': 'completed' if task_completion and task_completion.verified else 'pending' if task_completion else 'incomplete',
                'completion_date': task_completion.completion_date.strftime('%Y-%m-%d') if task_completion else None,
                'comment': task_completion.notes if task_completion else None,
                'attachment': task_completion.proof if task_completion else None
            },
            'team_progress': {
                'percentage': team_progress,
                'completed': completed_count,
                'total': team_total
            },
            'streak': streak,
            'active': is_active
        }
        
        tasks_data.append(task_data)
    
    # 按照完成状态和截止日期排序
    tasks_data.sort(key=lambda x: (
        x['player_completion']['status'] == 'completed',  # 未完成的排前面
        x['end_date'] if x['end_date'] else '9999-12-31'  # 截止日期近的排前面
    ))
    
    return JsonResponse({
        'code': 200,
        'message': '获取成功',
        'data': {
            'tasks': tasks_data
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def complete_task(request):
    """完成任务打卡"""
    # 添加调试输出
    auth_header = request.headers.get('Authorization')
    print(f"DEBUG - Auth header: {auth_header}")
    
    try:
        # 解析请求数据
        data = json.loads(request.body)
        player_id = data.get('player_id')
        task_id = data.get('task_id')
        comment = data.get('comment', '')
        attachment = data.get('attachment')
        
        if not player_id or not task_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数'
            }, status=400)
        
        # 验证token和获取队员
        player, error_response = verify_token_and_get_player(request, player_id)
        if error_response:
            return error_response
        
        # 验证任务是否存在
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '任务不存在'
            }, status=404)
        
        # 验证任务是否处于活跃状态
        if task.status != 'active':
            return JsonResponse({
                'code': 400,
                'message': '该任务已结束或未开始'
            }, status=400)
        
        # 验证任务是否在有效期内
        today = date.today()
        if task.end_date and task.end_date < today:
            return JsonResponse({
                'code': 400,
                'message': '该任务已过期'
            }, status=400)
        
        # 验证队员是否属于该任务的队伍 - 修复语法错误和字段引用
        if not player.teams.filter(id__in=task.teams.values_list('id', flat=True)).exists():
            return JsonResponse({
                'code': 403,
                'message': '该队员不属于任务队伍'
            }, status=403)
        
        # 检查是否已经完成过该任务
        if task.period == 'once':
            existing_completion = TaskCompletion.objects.filter(
                task=task,
                player=player,
                verified=True
            ).exists()
            
            if existing_completion:
                return JsonResponse({
                    'code': 400,
                    'message': '该任务已完成过'
                }, status=400)
        else:
            # 对于周期性任务，检查今天是否已经完成
            existing_completion = TaskCompletion.objects.filter(
                task=task,
                player=player,
                completion_date=today,
                verified=True
            ).exists()
            
            if existing_completion:
                return JsonResponse({
                    'code': 400,
                    'message': '今天已经完成过该任务'
                }, status=400)
        
        # 如果需要证明但没提供
        if task.require_proof and not attachment:
            status = 'pending'  # 设为待审核状态
        else:
            status = 'completed'  # 直接设为已完成
        
        # 创建任务完成记录
        completion = TaskCompletion.objects.create(
            task=task,
            player=player,
            comment=comment,
            attachment=attachment,
            status=status
        )
        
        # 获取连续完成天数
        streak = task.get_task_streak(player)
        
        # 获取团队完成情况 - 修复语法错误和逻辑
        team = task.teams.filter(players=player).first()
        team_total = team.players.count() if team else 0
        
        if team_total > 0:
            if task.period == 'once':
                completed_count = TaskCompletion.objects.filter(
                    task=task, 
                    verified=True
                ).values('player').distinct().count()
            else:
                completed_count = TaskCompletion.objects.filter(
                    task=task, 
                    verified=True,
                    completion_date=today
                ).values('player').distinct().count()
                
            team_progress = round((completed_count / team_total) * 100)
        else:
            completed_count = 0
            team_progress = 0
        
        return JsonResponse({
            'code': 200,
            'message': '打卡成功' if status == 'completed' else '打卡成功，等待审核',
            'data': {
                'completion_id': completion.id,
                'status': status,
                'completion_date': completion.completion_date.strftime('%Y-%m-%d'),
                'streak': streak,
                'team_progress': {
                    'percentage': team_progress,
                    'completed': completed_count,
                    'total': team_total
                }
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': '无效的请求数据格式'}, status=400)
    except Exception as e:
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_task_details(request):
    """获取任务详情，包括队伍完成情况"""
    task_id = request.GET.get('task_id')
    player_id = request.GET.get('player_id')
    
    if not task_id or not player_id:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'}, status=400)
        
    # 验证token和获取队员
    player, error_response = verify_token_and_get_player(request, player_id)
    if error_response:
        return error_response
    
    # 获取任务
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '任务不存在'}, status=404)
    
    # 验证队员是否属于任务队伍 - 修复语法错误
    if not player.teams.filter(id__in=task.teams.values_list('id', flat=True)).exists():
        return JsonResponse({'code': 403, 'message': '无权查看此任务详情'}, status=403)
        
    # 获取当前日期
    today = date.today()
    
    # 获取队员的完成情况
    if task.period == 'once':
        player_completion = TaskCompletion.objects.filter(
            task=task, 
            player=player
        ).order_by('-completion_date').first()
    else:
        player_completion = TaskCompletion.objects.filter(
            task=task, 
            player=player,
            completion_date=today
        ).first()
    
    # 获取任务连续完成天数
    streak = task.get_task_streak(player)
    
    # 获取队伍完成情况 - 需要修改
    # 找出与当前队员相关的第一个队伍
    team = task.teams.filter(players=player).first()
    if not team:
        return JsonResponse({'code': 404, 'message': '找不到相关队伍'}, status=404)
    
    team_members = team.players.all()
    
    # 获取队员完成情况
    team_completions = []
    
    for member in team_members:
        # 获取完成记录
        if task.period == 'once':
            completion = TaskCompletion.objects.filter(
                task=task, 
                player=member
            ).order_by('-completion_date').first()
        else:
            completion = TaskCompletion.objects.filter(
                task=task, 
                player=member,
                completion_date=today
            ).first()
        
        # 获取队员的连续完成天数
        member_streak = task.get_task_streak(member)
        
        member_data = {
            'player_id': member.id,
            'player_name': member.name,
            'streak': member_streak,
            'jersey_number': member.jersey_number,
            'status': completion.status if completion else 'incomplete',
            'completion_date': completion.completion_date.strftime('%Y-%m-%d') if completion else None,
            'streak': member_streak
        }
        
        team_completions.append(member_data)
    
    # 按照状态排序：已完成 > 待审核 > 未完成
    status_order = {'completed': 0, 'pending': 1, 'incomplete': 2}
    team_completions.sort(key=lambda x: (status_order.get(x['status'], 3), -x['streak']))
    
    # 任务基本信息 - 整理混乱的字段定义
    task_data = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'period': task.period,
        'start_date': task.start_date.strftime('%Y-%m-%d'),
        'end_date': task.end_date.strftime('%Y-%m-%d') if task.end_date else None,
        'points': task.points,
        'status': task.status,
        'require_proof': task.require_proof,
        'team_name': team.name,
        'task_type': {
            'name': task.task_type.name if hasattr(task, 'task_type') and task.task_type else None,
            'icon': task.task_type.icon if hasattr(task, 'task_type') and task.task_type else None,
            'color': task.task_type.color if hasattr(task, 'task_type') and task.task_type else None
        } if hasattr(task, 'task_type') and task.task_type else None,
        'player_completion': {
            'status': player_completion.status if player_completion else 'incomplete',
            'completion_date': player_completion.completion_date.strftime('%Y-%m-%d') if player_completion else None,
            'comment': player_completion.comment if player_completion else None,
            'attachment': player_completion.attachment if player_completion else None
        },
        'streak': streak,
        'team_completions': team_completions
    }
    
    return JsonResponse({
        'code': 200,
        'message': '获取成功',
        'data': task_data
    })

@csrf_exempt
@require_http_methods(["GET"])
def get_team_task_stats(request):
    """获取队伍任务统计数据"""
    player_id = request.GET.get('player_id')
    team_id = request.GET.get('team_id')
    
    if not player_id:
        return JsonResponse({'code': 400, 'message': '缺少player_id参数'}, status=400)
        
    # 验证token和获取队员
    player, error_response = verify_token_and_get_player(request, player_id)
    if error_response:
        return error_response
        
    # 如果没有指定队伍，获取队员的第一个队伍
    if not team_id:
        team = player.teams.first()
        if not team:
            return JsonResponse({'code': 404, 'message': '队员不属于任何队伍'}, status=404)
        team_id = team.id
    
    # 验证队员是否属于指定队伍
    if not player.teams.filter(id=team_id).exists():
        return JsonResponse({'code': 403, 'message': '无权查看此队伍数据'}, status=403)
    
    team = Team.objects.get(id=team_id)
    
    # 获取今天的日期
    today = date.today()
    
    # 获取团队活跃任务 - 修复字段引用错误
    active_tasks = Task.objects.filter(
        teams=team,  # 修改: 使用teams替代team
        status='active', 
        start_date__lte=today
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    
    # 获取每个任务的统计数据
    tasks_stats = []
    
    for task in active_tasks:
        # 获取队员数量
        team_size = team.players.count()
        
        # 获取已完成人数
        if task.period == 'once':
            completed_count = TaskCompletion.objects.filter(
                task=task, 
                verified=True,
                player__in=team.players.all()
            ).values('player').distinct().count()
        else:
            completed_count = TaskCompletion.objects.filter(
                task=task, 
                verified=True,
                completion_date=today,
                player__in=team.players.all()
            ).values('player').distinct().count()
        
        # 计算完成率
        completion_rate = round((completed_count / team_size) * 100) if team_size > 0 else 0
        
        # 当前队员是否完成
        if task.period == 'once':
            player_completed = TaskCompletion.objects.filter(
                task=task, 
                player=player,
                verified=True
            ).exists()
        else:
            player_completed = TaskCompletion.objects.filter(
                task=task, 
                player=player,
                completion_date=today,
                verified=True
            ).exists()
        
        # 队员任务连续完成天数
        streak = task.get_task_streak(player)
        
        # 排名数据 - 按连续完成天数排序
        players = team.players.all()
        player_streaks = [(p, task.get_task_streak(p)) for p in players]
        player_streaks.sort(key=lambda x: x[1], reverse=True)
        
        # 取连续天数前三的队员
        player_ranks = []
        for i, (p, p_streak) in enumerate(player_streaks[:3], 1):
            player_ranks.append({
                'rank': i,
                'player_id': p.id,
                'player_name': p.name,
                'avatar_url': p.avatar,
                'jersey_number': p.jersey_number,
                'streak': p_streak
            })
        
        # 当前任务统计
        task_stat = {
            'task_id': task.id,
            'title': task.title,
            'period': task.period,  # 使用period替代frequency
            'task_type': {
                'name': task.task_type.name,
                'icon': task.task_type.icon,
                'color': task.task_type.color
            } if task.task_type else None,
            'team_stats': {
                'completion_rate': completion_rate,
                'completed_count': completed_count,
                'team_size': team_size
            },
            'player_stats': {
                'completed': player_completed,
                'streak': streak
            },
            'top_players': player_ranks
        }
        
        tasks_stats.append(task_stat)
    
    # 按照任务类型分组 - 修复代码格式混乱
    task_type_stats = {}
    for task_stat in tasks_stats:
        task_type = (task_stat.get('task_type') or {}).get('name', '其他')
        if task_type not in task_type_stats:
            task_type_stats[task_type] = []
        task_type_stats[task_type].append(task_stat)
    
    # 团队整体数据
    team_data = {
        'id': team.id,
        'name': team.name,
        'task_count': active_tasks.count(),
        'player_count': team.players.count(),
        'task_type_stats': [
            {
                'type': type_name,
                'tasks': tasks
            }
            for type_name, tasks in task_type_stats.items()
        ]
    }
    
    return JsonResponse({
        'code': 200,
        'message': '获取成功',
        'data': team_data
    })

@csrf_exempt
@require_http_methods(["GET"])
def get_player_task_history(request):
    """获取某队员在指定日期范围内的任务完成记录
    接收参数:
    - player_id: 玩家ID (必填)
    - start_date: 开始日期 (可选, 默认为7天前)
    - end_date: 结束日期 (可选, 默认为今天)
    """
    player_id = request.GET.get('player_id')
    if not player_id:
        return JsonResponse({'code': 400, 'message': '缺少player_id参数'}, status=400)
    
    # 验证token和获取队员
    player, error_response = verify_token_and_get_player(request, player_id)
    if error_response:
        return error_response
    
    today = date.today()
    default_start = today - timedelta(days=7)
    
    start_date_str = request.GET.get('start_date', default_start.isoformat())
    end_date_str = request.GET.get('end_date', today.isoformat())
    
    try:
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'code': 400, 'message': '日期格式无效'}, status=400)
    
    completions = TaskCompletion.objects.filter(
        player=player,
        completion_date__range=(start_date_obj, end_date_obj)
    ).select_related('task').order_by('-completion_date')
    
    data_list = []
    for comp in completions:
        data_list.append({
            'task_id': comp.task.id,
            'title': comp.task.title,
            'completion_date': comp.completion_date.strftime('%Y-%m-%d'),
            'status': comp.status,
            'comment': comp.comment,
            'attachment': comp.attachment
        })
    
    return JsonResponse({
        'code': 200,
        'message': '获取成功',
        'data': {
            'player_id': player.id,
            'history': data_list
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def update_task_completion_status(request):
    """
    更新任务完成记录的状态
    接收参数:
    - completion_id: 任务完成记录ID (必填)
    - new_status: 新的状态, 可为 'completed' 或 'rejected'
    """
    try:
        body_data = json.loads(request.body)
        completion_id = body_data.get('completion_id')
        new_status = body_data.get('new_status')
    except:
        return JsonResponse({'code': 400, 'message': '无效的请求数据'}, status=400)
    
    if not completion_id or not new_status:
        return JsonResponse({'code': 400, 'message': '缺少必要参数'}, status=400)
    
    if new_status not in ['completed', 'rejected']:
        return JsonResponse({'code': 400, 'message': '状态无效'}, status=400)
    
    # 验证token仅需保证是家长即可
    _, error_response = verify_token_and_get_player(request)
    if error_response:
        return error_response
    
    try:
        completion = TaskCompletion.objects.get(id=completion_id)
    except TaskCompletion.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '任务完成记录不存在'}, status=404)
    
    # 更新状态
    completion.status = new_status
    completion.save()
    
    return JsonResponse({
        'code': 200,
        'message': '更新成功',
        'data': {
            'completion_id': completion.id,
            'new_status': completion.status
        }
    })

@csrf_exempt
@require_http_methods(["POST"])
def assign_task_to_team(request):
    """将任务分配给队伍"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        team_id = data.get('team_id')
        action = data.get('action', 'add')  # 新增参数: 'add'添加队伍, 'remove'移除队伍
        
        if not task_id or not team_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少必要参数'
            }, status=400)
        
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({'code': 401, 'message': '未登录'}, status=401)
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'coach':
                return JsonResponse({'code': 403, 'message': '无权分配任务'}, status=403)
            coach_id = payload.get('user_id')
        except (jwt.InvalidTokenError, Coach.DoesNotExist):
            return JsonResponse({'code': 401, 'message': '无效的token或教练不存在'}, status=401)
        
        # 验证任务和队伍是否存在
        try:
            task = Task.objects.get(id=task_id)
            team = Team.objects.get(id=team_id)
        except (Task.DoesNotExist, Team.DoesNotExist):
            return JsonResponse({
                'code': 404,
                'message': '任务或队伍不存在'
            }, status=404)
        
        if not (team.head_coach.id == coach_id or team.coaches.filter(id=coach_id).exists()):
            return JsonResponse({
                'code': 403,
                'message': '您不是该队伍的教练，无权分配任务'
            }, status=403)
        
        # 更新任务的队伍关系
        if action == 'add':
            task.teams.add(team)
            message = '任务分配成功'
        elif action == 'remove':
            task.teams.remove(team)
            message = '任务移除成功'
        else:
            return JsonResponse({
                'code': 400,
                'message': '无效的action参数'
            }, status=400)
        
        return JsonResponse({
            'code': 200,
            'message': message,
            'data': {
                'task_id': task.id,
                'team_id': team.id,
                'team_name': team.name,
                'task_title': task.title,
                'teams': [{'id': t.id, 'name': t.name} for t in task.teams.all()]
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': '无效的请求数据格式'}, status=400)
    except Exception as e:
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'}, status=500)

# 在文件末尾添加测试接口
@csrf_exempt
@require_http_methods(["GET"])
def debug_player_tasks(request):
    """调试接口：获取指定队员的任务数据"""
    try:
        player_id = request.GET.get('player_id')
        
        if not player_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少player_id参数'
            })
            
        # 查询队员是否存在
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': f'找不到ID为{player_id}的队员'
            })
        
        # 获取队员所在的队伍
        teams = player.teams.all()
        team_ids = list(teams.values_list('id', flat=True))
        
        # 获取分配给这些队伍的任务
        tasks = Task.objects.filter(teams__in=teams).distinct()
        task_count = tasks.count()
        
        # 调试信息
        debug_info = {
            'player_name': player.name,
            'team_count': teams.count(),
            'team_ids': team_ids,
            'team_names': list(teams.values_list('name', flat=True)),
            'task_ids': list(tasks.values_list('id', flat=True)),
            'task_count': task_count,
            'task_titles': list(tasks.values_list('title', flat=True))
        }
        
        return JsonResponse({
            'code': 200,
            'message': '调试信息获取成功',
            'data': debug_info
        })
    except Exception as e:
        logger.error(f"调试接口出错: {str(e)}")
        return JsonResponse({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        })
