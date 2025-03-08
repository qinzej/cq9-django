from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Parent, Coach, School, EnrollmentYear, Player
import json
import jwt
from datetime import datetime, timedelta
from django.conf import settings

def generate_token(user_id, user_type):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(days=30)  # token有效期30天
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

@csrf_exempt
@require_http_methods(["POST"])
def parent_register(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        password = data.get('password')

        if not phone or not password:
            return JsonResponse({
                'code': 400,
                'message': '手机号和密码不能为空'
            }, status=400)

        # 验证手机号格式
        if not phone.isdigit() or len(phone) != 11:
            return JsonResponse({
                'code': 400,
                'message': '手机号格式不正确'
            }, status=400)

        # 验证密码长度
        if len(password) < 6:
            return JsonResponse({
                'code': 400,
                'message': '密码长度不能少于6位'
            }, status=400)

        # 检查手机号是否已注册
        if Parent.objects.filter(phone=phone).exists():
            return JsonResponse({
                'code': 400,
                'message': '该手机号已注册'
            }, status=400)

        # 创建新家长账号
        parent = Parent.objects.create(
            phone=phone,
            miniprogram_password=password
        )

        # 生成token
        token = generate_token(parent.id, 'parent')

        # 获取关联的队员信息
        players = []

        # 返回注册成功信息，包含token和user_info
        return JsonResponse({
            'code': 200,
            'message': '注册成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': parent.id,
                    'name': parent.name,
                    'phone': parent.phone,
                    'type': 'parent',
                    'players': players
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_schools(request):
    try:
        schools = School.objects.all()
        school_list = [{
            'id': school.id,
            'name': school.name
        } for school in schools]

        return JsonResponse({
            'code': 200,
            'message': '获取成功',
            'data': school_list
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_enrollment_years(request):
    try:
        years = EnrollmentYear.objects.all()
        year_list = [{
            'id': year.id,
            'year': year.year
        } for year in years]

        return JsonResponse({
            'code': 200,
            'message': '获取成功',
            'data': year_list
        })
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

def search_players(request):
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'parent':
                raise jwt.InvalidTokenError
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 获取请求数据
        name = request.GET.get('name', '')

        if not name:
            return JsonResponse({
                'code': 400,
                'message': '请输入队员姓名'
            }, status=400)

        # 查询队员
        players = Player.objects.filter(name__icontains=name)
        
        # 转换为JSON格式
        players_data = [{
            'id': player.id,
            'name': player.name,
            'school': player.school.name,
            'enrollment_year': player.enrollment_year.year,
            'jersey_number': player.jersey_number
        } for player in players]

        return JsonResponse({
            'code': 200,
            'message': '查询成功',
            'data': players_data
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def unbind_player(request):
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'parent':
                raise jwt.InvalidTokenError
            parent_id = payload.get('user_id')
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 获取请求数据
        data = json.loads(request.body)
        player_id = data.get('player_id')

        if not player_id:
            return JsonResponse({
                'code': 400,
                'message': '请选择要解绑的队员'
            }, status=400)

        try:
            # 获取家长和队员
            parent = Parent.objects.get(id=parent_id)
            player = Player.objects.get(id=player_id)

            # 检查队员是否属于当前家长
            if parent not in player.parents.all():
                return JsonResponse({
                    'code': 403,
                    'message': '无权解绑该队员'
                }, status=403)

            # 解绑队员
            player.parents.remove(parent)

            # 获取更新后的家长信息
            players = [{
                'id': p.id,
                'name': p.name,
                'school': p.school.name,
                'enrollment_year': p.enrollment_year.year
            } for p in parent.players.all()]

            return JsonResponse({
                'code': 200,
                'message': '解绑成功',
                'data': {
                    'players': players
                }
            })

        except Parent.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '家长不存在'
            }, status=404)
        except Player.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '队员不存在'
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bind_player(request):
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'parent':
                raise jwt.InvalidTokenError
            parent_id = payload.get('user_id')
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 获取请求数据
        data = json.loads(request.body)
        player_id = data.get('player_id')

        if not player_id:
            return JsonResponse({
                'code': 400,
                'message': '请选择要绑定的队员'
            }, status=400)

        try:
            # 获取家长和队员
            parent = Parent.objects.get(id=parent_id)
            player = Player.objects.get(id=player_id)

            # 检查家长已绑定的队员数量
            if parent.players.count() >= 3:
                return JsonResponse({
                    'code': 400,
                    'message': '每位家长最多只能绑定3个队员'
                }, status=400)

            # 检查队员已绑定的家长数量
            if player.parents.count() >= 6:
                return JsonResponse({
                    'code': 400,
                    'message': '每位队员最多可以被6位家长绑定'
                }, status=400)

            # 绑定队员
            player.parents.add(parent)

            # 获取更新后的家长信息
            players = [{
                'id': p.id,
                'name': p.name,
                'school': p.school.name,
                'enrollment_year': p.enrollment_year.year
            } for p in parent.players.all()]

            return JsonResponse({
                'code': 200,
                'message': '绑定成功',
                'data': {
                    'players': players
                }
            })

        except Parent.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '家长不存在'
            }, status=404)
        except Player.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '队员不存在'
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def parent_login(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        password = data.get('password')

        if not phone or not password:
            return JsonResponse({
                'code': 400,
                'message': '手机号和密码不能为空'
            }, status=400)

        # 查找家长
        try:
            parent = Parent.objects.get(phone=phone)
        except Parent.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '该手机号未注册'
            }, status=404)

        # 验证密码
        if parent.miniprogram_password != password:
            return JsonResponse({
                'code': 401,
                'message': '密码错误'
            }, status=401)

        # 生成token
        token = generate_token(parent.id, 'parent')

        # 获取关联的队员信息
        players = [{
            'id': player.id,
            'name': player.name,
            'school': player.school.name,
            'enrollment_year': player.enrollment_year.year,
            'jersey_number': player.jersey_number
        } for player in parent.players.all()]

        # 登录成功，返回家长信息和token
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': parent.id,
                    'name': parent.name,
                    'phone': parent.phone,
                    'type': 'parent',
                    'players': players
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def coach_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                'code': 400,
                'message': '用户名和密码不能为空'
            }, status=400)

        # 验证教练用户
        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({
                'code': 401,
                'message': '用户名或密码错误'
            }, status=401)

        # 检查用户是否是教练
        try:
            coach = Coach.objects.get(user=user)
            if not coach.is_active:
                return JsonResponse({
                    'code': 403,
                    'message': '该账号已被禁用'
                }, status=403)
        except Coach.DoesNotExist:
            return JsonResponse({
                'code': 403,
                'message': '该用户不是教练'
            }, status=403)

        # 生成token
        token = generate_token(coach.id, 'coach')

        # 登录成功，返回教练信息和token
        return JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user_info': {
                    'id': coach.id,
                    'username': user.username,
                    'name': user.get_full_name() or user.username,
                    'phone': coach.phone,
                    'type': 'coach',
                    'speciality': coach.speciality
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def parent_dashboard(request):
    try:
        # 验证token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'code': 401, 'message': '未提供有效凭证'}, status=401)
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if not payload or payload.get('type') != 'parent':
            return JsonResponse({'code': 403, 'message': '无访问权限'}, status=403)

        # 获取家长信息
        parent = Parent.objects.get(id=payload['user_id'])
        
        # 获取关联队员的最新训练数据
        players_data = []
        for player in parent.players.all():
            players_data.append({
                'name': player.name,
                'attendance': player.get_attendance_rate(),
                'latest_skills': player.get_latest_skills(),
                'next_session': player.get_next_session_info()
            })

        # 获取关联课程信息
        courses = [{
            'id': session.id,
            'name': session.course.name,
            'time': session.schedule,
            'coach': session.coach.name
        } for session in TrainingSession.objects.filter(players__in=parent.players.all()).distinct()]

        return JsonResponse({
            'code': 200,
            'data': {
                'child_progress': players_data,
                'courses': courses
            }
        })

    except Exception as e:
        return JsonResponse({'code': 500, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_player(request):
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'parent':
                raise jwt.InvalidTokenError
            parent_id = payload.get('user_id')
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 获取请求数据
        data = json.loads(request.body)
        name = data.get('name')
        school_id = data.get('school_id')
        enrollment_year_id = data.get('enrollment_year_id')
        avatar_url = data.get('avatar_url')  # 这里已经支持接收avatar_url

        # 验证必填字段
        if not name or not school_id or not enrollment_year_id:
            return JsonResponse({
                'code': 400,
                'message': '请填写完整的队员信息'
            }, status=400)

        try:
            # 获取家长、学校和入学年份
            parent = Parent.objects.get(id=parent_id)
            school = School.objects.get(id=school_id)
            enrollment_year = EnrollmentYear.objects.get(id=enrollment_year_id)

            # 检查是否已存在相同信息的队员
            existing_player = Player.objects.filter(
                name=name,
                school=school,
                enrollment_year=enrollment_year
            ).first()

            if existing_player:
                return JsonResponse({
                    'code': 400,
                    'message': '该队员信息已存在'
                }, status=400)

            # 创建新队员
            player = Player.objects.create(
                name=name,
                school=school,
                enrollment_year=enrollment_year,
                avatar=avatar_url,  # 这里已经支持存储avatar_url
                jersey_number=data.get('jersey_number')
            )

            # 建立家长和队员的关联关系
            player.parent = parent
            player.save()

            return JsonResponse({
                'code': 200,
                'message': '添加队员成功',
                'data': {
                    'id': player.id,
                    'name': player.name,
                    'school': player.school.name,
                    'enrollment_year': player.enrollment_year.year,
                    'avatar': player.avatar
                }
            })

        except (School.DoesNotExist, EnrollmentYear.DoesNotExist):
            return JsonResponse({
                'code': 400,
                'message': '学校或入学年份不存在'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_player(request):
    try:
        # 验证token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return JsonResponse({
                'code': 401,
                'message': '未登录'
            }, status=401)

        # 解析token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('user_type') != 'parent':
                raise jwt.InvalidTokenError
            parent_id = payload.get('user_id')
        except jwt.InvalidTokenError:
            return JsonResponse({
                'code': 401,
                'message': '无效的token'
            }, status=401)

        # 获取请求数据
        data = json.loads(request.body)
        player_id = data.get('player_id')
        
        if not player_id:
            return JsonResponse({
                'code': 400,
                'message': '缺少队员ID'
            }, status=400)
            
        # 检查是否有更新的字段
        updatable_fields = {
            'name': data.get('name'),
            'school_id': data.get('school_id'),
            'enrollment_year_id': data.get('enrollment_year_id'),
            'jersey_number': data.get('jersey_number'),
            'avatar_url': data.get('avatar_url')
        }
        
        # 过滤掉None值，只保留需要更新的字段
        fields_to_update = {k: v for k, v in updatable_fields.items() if v is not None}
        
        if not fields_to_update:
            return JsonResponse({
                'code': 400,
                'message': '没有提供需要更新的字段'
            }, status=400)

        try:
            # 获取家长和队员
            parent = Parent.objects.get(id=parent_id)
            player = Player.objects.get(id=player_id)
            
            # 验证权限：检查队员是否属于当前家长
            if parent not in player.parents.all():
                return JsonResponse({
                    'code': 403,
                    'message': '您没有权限更新该队员信息'
                }, status=403)
            
            # 更新字段
            if 'name' in fields_to_update:
                player.name = fields_to_update['name']
                
            if 'school_id' in fields_to_update:
                try:
                    school = School.objects.get(id=fields_to_update['school_id'])
                    player.school = school
                except School.DoesNotExist:
                    return JsonResponse({
                        'code': 400,
                        'message': '所选学校不存在'
                    }, status=400)
                    
            if 'enrollment_year_id' in fields_to_update:
                try:
                    enrollment_year = EnrollmentYear.objects.get(id=fields_to_update['enrollment_year_id'])
                    player.enrollment_year = enrollment_year
                except EnrollmentYear.DoesNotExist:
                    return JsonResponse({
                        'code': 400,
                        'message': '所选入学年份不存在'
                    }, status=400)
            
            if 'jersey_number' in fields_to_update:
                player.jersey_number = fields_to_update['jersey_number']
                
            if 'avatar_url' in fields_to_update:
                player.avatar = fields_to_update['avatar_url']
                
            # 保存更新
            player.save()
            
            # 返回更新后的队员信息
            updated_player = {
                'id': player.id,
                'name': player.name,
                'school': player.school.name,
                'school_id': player.school.id,
                'enrollment_year': player.enrollment_year.year,
                'enrollment_year_id': player.enrollment_year.id,
                'jersey_number': player.jersey_number,
                'avatar_url': player.avatar
            }
            
            # 直接从数据库重新查询所有关联的队员
            all_players = Player.objects.filter(parents=parent)
            
            players = [{
                'id': p.id,
                'name': p.name,
                'school': p.school.name,
                'enrollment_year': p.enrollment_year.year,
                'jersey_number': p.jersey_number,
                'avatar_url': p.avatar
            } for p in all_players]
            
            return JsonResponse({
                'code': 200,
                'message': '队员信息更新成功',
                'data': {
                    'player': updated_player,
                    'players': players
                }
            })

        except Parent.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '家长信息不存在'
            }, status=404)
        except Player.DoesNotExist:
            return JsonResponse({
                'code': 404,
                'message': '队员不存在'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'message': '无效的请求数据格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'更新队员信息失败: {str(e)}'
        }, status=500)