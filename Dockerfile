# 使用 Python 3.10 的官方镜像
FROM python:3.10-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖 - 添加pkg-config
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    netcat-openbsd \
    curl \
    iproute2 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并设置工作目录
COPY requirements.txt /app/
WORKDIR /app

# 配置MySQL客户端编译环境变量
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib/x86_64-linux-gnu -lmysqlclient"

# 添加PyMySQL到依赖中，因为代码中仍然导入它
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn whitenoise PyMySQL

# 复制项目文件
COPY . /app

# 创建静态文件目录
RUN mkdir -p staticfiles

# 尝试收集静态文件，如果失败则创建空文件以继续构建
RUN python3 manage.py collectstatic --noinput || touch staticfiles/.keep

# 添加数据库迁移脚本
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# 修改 HEALTHCHECK 使用专门的健康检查端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=5 \
  CMD curl -f http://localhost:80/health/ || exit 1

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]