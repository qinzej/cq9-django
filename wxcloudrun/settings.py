import os
from pathlib import Path
import time

CUR_PATH = os.path.dirname(os.path.realpath(__file__))  
LOG_PATH = os.path.join(os.path.dirname(CUR_PATH), 'logs') # LOG_PATH是存放日志的路径
if not os.path.exists(LOG_PATH): os.mkdir(LOG_PATH)  # 如果不存在这个logs文件夹，就自动创建一个

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_&03zc)d*3)w-(0grs-+t-0jjxktn7k%$3y6$9=x_n_ibg4js6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'wxcloudrun'
]

# SimpleUI 配置
SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menu_display': ['管理员管理', '队员管理', '队伍管理', '任务管理', '成就管理', '考核管理', '系统管理'],
    'dynamic': True,
    'site_title': '超群九人后台管理',
    'site_header': '超群九人后台管理',
    'title': '超群九人后台管理',
    'menu_style': 'light',
    'home_page': '',
    'home_title': '',
    'home_info': False,
    'menus': [{
        'name': '任务管理',
        'icon': 'fas fa-tasks',
        'models': [
            {
                'name': '任务',
                'icon': 'fas fa-clipboard-list',
                'url': 'wxcloudrun/task/'
            },
            {
                'name': '任务完成记录',
                'icon': 'fas fa-check-square',
                'url': 'wxcloudrun/taskcompletion/'
            }
        ]
    },
    {
        'name': '成就管理',
        'icon': 'fas fa-trophy',
        'models': [
            {
                'name': '成就类别',
                'icon': 'fas fa-star',
                'url': 'wxcloudrun/achievementcategory/'
            },
            {
                'name': '个人成就',
                'icon': 'fas fa-medal',
                'url': 'wxcloudrun/personalachievement/'
            },
            {
                'name': '队员成就记录',
                'icon': 'fas fa-award',
                'url': 'wxcloudrun/playerachievement/'
            },
            {
                'name': '队伍成就',
                'icon': 'fas fa-crown',
                'url': 'wxcloudrun/teamachievement/'
            }
        ]
    },
    {
        'name': '考核管理',
        'icon': 'fas fa-clipboard-check',
        'models': [
            {
                'name': '考核',
                'icon': 'fas fa-file-alt',
                'url': 'wxcloudrun/assessment/'
            },
            {
                'name': '考核项目',
                'icon': 'fas fa-list-alt',
                'url': 'wxcloudrun/assessmentitem/'
            },
            {
                'name': '考核成绩',
                'icon': 'fas fa-chart-bar',
                'url': 'wxcloudrun/assessmentscore/'
            }
        ]
    },
    {
        'name': '队伍管理',
        'icon': 'fas fa-users-cog',
        'models': [
            {
                'name': '队伍信息',
                'icon': 'fas fa-users',
                'url': 'wxcloudrun/team/'
            }
        ]
    },
    {
        'name': '管理员管理',
        'icon': 'fas fa-users-cog',
        'models': [
            {
                'name': '用户',
                'icon': 'fas fa-user',
                'url': 'auth/user/'
            },
            {
                'name': '用户组',
                'icon': 'fas fa-users',
                'url': 'auth/group/'
            }
        ]
    },
    {
        'name': '队员管理',
        'icon': 'fas fa-users',
        'models': [
            {
                'name': '队员信息',
                'icon': 'fas fa-user',
                'url': 'wxcloudrun/player/'
            },
            {
                'name': '家长信息',
                'icon': 'fas fa-user-friends',
                'url': 'wxcloudrun/parent/'
            }
        ]
    },
    {
        'name': '系统管理',
        'icon': 'fas fa-cogs',
        'models': [
            {
                'name': '入学年份',
                'icon': 'fas fa-calendar',
                'url': 'wxcloudrun/enrollmentyear/'
            },
            {
                'name': '学校',
                'icon': 'fas fa-school',
                'url': 'wxcloudrun/school/'
            }
        ]
    }]
}

SIMPLEUI_HOME_INFO = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wxcloudrun.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wxcloudrun.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("MYSQL_DATABASE", 'django_demo'),
        'USER': os.environ.get("MYSQL_USERNAME", 'root'),
        'HOST': os.environ.get("MYSQL_ADDRESS", 'localhost:3306').split(':')[0],
        'PORT': os.environ.get("MYSQL_ADDRESS", 'localhost:3306').split(':')[1],
        'PASSWORD': os.environ.get("MYSQL_PASSWORD", ''),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        # 日志格式
        'standard': {
            'format': '[%(asctime)s] [%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] '
                      '[%(levelname)s]- %(message)s'},
        'simple': {  # 简单格式
            'format': '%(levelname)s %(message)s'
        },
    },
    # 过滤
    'filters': {
    },
    # 定义具体处理日志的方式
    'handlers': {
        # 默认记录所有日志
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'all-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'standard',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
        },
        # 输出错误日志
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'error-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 5,  # 备份数
            'formatter': 'standard',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
        },
        # 控制台输出
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        # 输出info日志
        'info': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'info-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'standard',
            'encoding': 'utf-8',  # 设置默认编码
        },
    },
    # 配置用哪几种 handlers 来处理日志
    'loggers': {
        # 类型 为 django 处理所有类型的日志， 默认调用
        'django': {
            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        # log 调用时需要当作参数传入
        'log': {
            'handlers': ['error', 'info', 'console', 'default'],
            'level': 'INFO',
            'propagate': True
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

# 生产环境静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 添加 WhiteNoise 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 新增
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

APPEND_SLASH = False

# 配置 WhiteNoise 压缩和缓存
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1年缓存

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGS_DIR = '/data/logs/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')