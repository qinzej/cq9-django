#!/bin/sh

# 等待数据库就绪
echo "Waiting for MySQL to be ready..."
while ! nc -z $MYSQL_ADDRESS $MYSQL_PORT; do
  sleep 1
done
echo "MySQL is ready"

# 执行数据库迁移
echo "Running database migrations..."
python3 manage.py migrate

# 启动 Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:80 --workers 4 wxcloudrun.wsgi:application