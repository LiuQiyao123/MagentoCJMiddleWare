#!/bin/bash

# WSL环境部署脚本
set -e

echo "🚀 开始WSL环境部署..."

# 更新系统包
echo "📦 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
echo "🔧 安装系统依赖..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 安装Docker
echo "🐳 安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "✅ Docker安装完成"
else
    echo "✅ Docker已安装"
fi

# 安装Docker Compose
echo "📦 安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose安装完成"
else
    echo "✅ Docker Compose已安装"
fi

# 启动Docker服务
echo "🔧 启动Docker服务..."
sudo service docker start

# 创建项目目录
echo "📁 创建项目目录..."
PROJECT_DIR="/home/$USER/MagentoCJMiddleWare"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 设置环境变量
echo "⚙️ 配置环境变量..."
cat > ~/.bashrc << 'EOF'
# 项目环境变量
export PROJECT_DIR="/home/$USER/MagentoCJMiddleWare"
export PATH="$PROJECT_DIR/scripts:$PATH"

# Docker别名
alias dc="docker-compose"
alias dcu="docker-compose up"
alias dcd="docker-compose down"
alias dcb="docker-compose build"
alias dcr="docker-compose restart"

# 项目别名
alias mw="cd $PROJECT_DIR"
alias mwlogs="cd $PROJECT_DIR/logs"
alias mwstart="$PROJECT_DIR/scripts/start.sh"
alias mwstop="$PROJECT_DIR/scripts/stop.sh"
alias mwstatus="$PROJECT_DIR/scripts/status.sh"
EOF

# 重新加载bashrc
source ~/.bashrc

echo "✅ WSL环境准备完成！"
echo "📝 请重新登录或运行: source ~/.bashrc"
echo "🚀 接下来请运行: ./scripts/deploy.sh" 