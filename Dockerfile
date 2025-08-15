# 1. 使用官方的、轻量的 Python 3.11 镜像作为基础
FROM python:3.11-slim

# 2. 设置环境变量，防止 Python 写入 .pyc 文件并配置路径
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. 在容器内部创建一个工作目录
WORKDIR /app

# 4. 复制依赖描述文件
COPY requirements.txt .

# 5. 在容器内安装所有依赖，使用国内镜像源加速
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 复制项目的所有代码到容器的工作目录
COPY . .

# 7. 容器启动时要执行的命令
# 告诉 uvicorn 监听所有网络接口的 8000 端口
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 