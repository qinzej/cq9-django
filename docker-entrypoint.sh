#!/bin/sh

# 设置最大重试次数和间隔时间
MAX_RETRIES=30
RETRY_INTERVAL=5

# 等待数据库就绪
echo "Waiting for MySQL to be ready..."
retry_count=0
until nc -z $MYSQL_ADDRESS $MYSQL_PORT || [ $retry_count -eq $MAX_RETRIES ]; do
    echo "Attempt $((retry_count+1))/$MAX_RETRIES: MySQL is unavailable - sleeping $RETRY_INTERVAL seconds"
    sleep $RETRY_INTERVAL
    retry_count=$((retry_count+1))
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "Could not connect to MySQL after $MAX_RETRIES attempts!"
    exit 1
fi

echo "MySQL is ready"

# 执行数据库迁移
echo "Running database migrations..."
python3 manage.py migrate || {
    echo "Database migration failed!"
    exit 1
}

# 收集静态文件（如果需要）
echo "Collecting static files..."
python3 manage.py collectstatic --noinput || {
    echo "Static files collection failed!"
    exit 1
}

# 可选：添加启动延迟，若需要等待其它依赖启动
echo "Waiting for 10 seconds before starting Gunicorn..."
sleep 10

# 启动 Gunicorn（直接 exec，使其成为主进程）
echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:80 \
    --workers 4 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output \
    --preload \
    wxcloudrun.wsgi:application
