#!/bin/sh

# 数据库迁移
echo "执行数据库迁移..."
python3 manage.py migrate || {
    echo "数据库迁移失败！"
    exit 1
}

# 收集静态文件
echo "收集静态文件..."
python3 manage.py collectstatic --noinput || {
    echo "静态文件收集失败！"
    exit 1
}

# 启动Gunicorn服务
echo "启动Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:80 \
    --workers 2 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wxcloudrun.wsgi:application