"""
核心安全模块：密码哈希、数据加密等
"""
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.config.settings import get_settings

settings = get_settings()

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fernet 对称加密密钥
# SECRET_KEY 必须是32字节的URL安全base64编码字符串
# 可以通过 Fernet.generate_key() 生成
_fernet = Fernet(settings.SECRET_KEY.encode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希密码匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    return pwd_context.hash(password)


def encrypt_data(data: str) -> str:
    """使用 Fernet 加密数据"""
    if not data:
        return ""
    return _fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """使用 Fernet 解密数据"""
    if not encrypted_data:
        return ""
    return _fernet.decrypt(encrypted_data.encode()).decode() 