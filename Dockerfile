# 二开推荐阅读[如何提高项目构建效率](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/scene/build/speed.html)
# 选择构建用基础镜像（选择原则：在包含所有用到的依赖前提下尽可能体积小）。如需更换，请到[dockerhub官方仓库](https://hub.docker.com/_/python?tab=tags)自行选择后替换。
# 已知alpine镜像与pytorch有兼容性问题会导致构建失败，如需使用pytorch请务必按需更换基础镜像。
FROM alpine:3.13

# 设置时区
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

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

# 拷贝当前项目到/app目录下(.dockerignore中文件除外)
COPY . /app
WORKDIR /app

# 安装 Python 依赖
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --user -r requirements.txt \
    && pip install gunicorn

# 创建静态文件目录并收集静态文件
RUN mkdir -p staticfiles && \
    python3 manage.py collectstatic --noinput

# 添加数据库迁移脚本
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# 使用入口脚本替代直接运行
ENTRYPOINT ["/docker-entrypoint.sh"]
