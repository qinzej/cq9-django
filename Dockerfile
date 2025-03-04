# 二开推荐阅读[如何提高项目构建效率](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/scene/build/speed.html)
# 选择构建用基础镜像（选择原则：在包含所有用到的依赖前提下尽可能体积小）。如需更换，请到[dockerhub官方仓库](https://hub.docker.com/_/python?tab=tags)自行选择后替换。
# 已知alpine镜像与pytorch有兼容性问题会导致构建失败，如需使用pytorch请务必按需更换基础镜像。
FROM alpine:3.13

# 设置时区
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

# 使用腾讯云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.cloud.tencent.com/g' /etc/apk/repositories

# 安装系统依赖
RUN apk add --update --no-cache \
    python3 \
    py3-pip \
    gcc \
    python3-dev \
    musl-dev \
    mariadb-dev \
    jpeg-dev \
    zlib-dev \
    libffi-dev \
    ca-certificates \
    netcat-openbsd \
    && rm -rf /var/cache/apk/*

# 先复制 requirements.txt
COPY requirements.txt /app/
WORKDIR /app

# 配置 pip 并安装依赖
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# 复制项目文件
COPY . /app

# 创建静态文件目录并收集静态文件
RUN mkdir -p staticfiles && \
    python3 manage.py collectstatic --noinput

# 添加数据库迁移脚本
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
