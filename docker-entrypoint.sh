#!/bin/sh

# 设置最大重试次数和间隔时间
MAX_RETRIES=30
RETRY_INTERVAL=5

# 设置MySQL默认端口（如果环境变量未定义）
MYSQL_PORT=${MYSQL_PORT:-3306}

# 网络诊断日志（改用替代命令）
echo "=== 网络诊断开始 ==="
echo "主机名: $(hostname)"
echo "IP地址: $(hostname -I)"
echo "路由表:"
route -n  # 使用route替代ip route
echo "DNS配置:"
cat /etc/resolv.conf
echo "=== 网络诊断结束 ==="

# 添加环境变量校验
if [ -z "$MYSQL_ADDRESS" ]; then
    echo "错误：必须设置 MYSQL_ADDRESS 环境变量"
    exit 1
fi

# 等待数据库就绪（使用带引号的变量）
until nc -zv "$MYSQL_ADDRESS" "$MYSQL_PORT" || [ $retry_count -eq $MAX_RETRIES ]; do
    echo "尝试 $((retry_count+1))/$MAX_RETRIES: MySQL不可用 - 等待 $RETRY_INTERVAL 秒"
    sleep $RETRY_INTERVAL
    retry_count=$((retry_count+1))
done

if [ $retry_count -eq $MAX_RETRIES ]; then
    echo "无法连接MySQL，已达最大重试次数！"
    exit 1
fi
echo "MySQL已就绪"

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