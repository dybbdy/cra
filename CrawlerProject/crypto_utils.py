"""
加密与隐私保护工具模块。

功能包括：
1. 姓名脱敏
2. AES-256-CBC 电话加密/解密
3. HMAC-SHA256 完整性校验
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Union

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# 课程实验演示用默认密钥。
# 实际生产环境应通过环境变量或密钥管理系统安全下发。
DEFAULT_AES_KEY = hashlib.sha256("CrawlerProject-AES-256-Key".encode("utf-8")).digest()
DEFAULT_HMAC_KEY = hashlib.sha256("CrawlerProject-HMAC-Key".encode("utf-8")).digest()


def _normalize_key(key: Union[str, bytes, None], default_key: bytes, expect_len: int = 32) -> bytes:
    """
    规范化密钥长度。

    参数：
        key: 输入密钥，支持 str / bytes / None
        default_key: 默认密钥
        expect_len: 期望字节长度，AES-256 为 32 字节

    返回：
        规范化后的 bytes 密钥
    """
    if key is None:
        return default_key

    if isinstance(key, str):
        key_bytes = key.encode("utf-8")
    else:
        key_bytes = key

    if len(key_bytes) == expect_len:
        return key_bytes

    return hashlib.sha256(key_bytes).digest()


def mask_name(name: str) -> str:
    """
    对姓名进行脱敏，只保留姓氏，其余字符替换为 * 。

    示例：
        张三 -> 张*
        欧阳娜娜 -> 欧***
    """
    if not name:
        return ""

    normalized_name = name.strip()
    if not normalized_name:
        return ""

    family_name = normalized_name[0]
    return family_name + ("*" * max(len(normalized_name) - 1, 0))


def encrypt_phone(phone: str, key: Union[str, bytes, None] = None) -> str:
    """
    使用 AES-256-CBC 加密手机号。

    参数：
        phone: 明文手机号
        key: 32字节密钥，未提供时使用默认实验密钥

    返回：
        Base64 编码的字符串，内容为 IV + 密文
    """
    if phone is None:
        raise ValueError("手机号不能为空")

    aes_key = _normalize_key(key, DEFAULT_AES_KEY, 32)
    iv = os.urandom(16)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(phone.encode("utf-8"), AES.block_size))
    return base64.b64encode(iv + ciphertext).decode("utf-8")


def decrypt_phone(cipher_text_base64: str, key: Union[str, bytes, None] = None) -> str:
    """
    解密手机号，主要用于测试验证。
    """
    if not cipher_text_base64:
        raise ValueError("密文不能为空")

    aes_key = _normalize_key(key, DEFAULT_AES_KEY, 32)
    raw = base64.b64decode(cipher_text_base64)
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    plain = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plain.decode("utf-8")


def generate_hmac(data: str, key: Union[str, bytes, None] = None) -> str:
    """
    使用 HMAC-SHA256 生成完整性校验码。

    参数：
        data: 待认证字符串
        key: HMAC 密钥，未提供时使用默认实验密钥

    返回：
        十六进制字符串
    """
    if data is None:
        raise ValueError("待认证数据不能为空")

    hmac_key = _normalize_key(key, DEFAULT_HMAC_KEY, 32)
    return hmac.new(hmac_key, data.encode("utf-8"), hashlib.sha256).hexdigest()


__all__ = [
    "mask_name",
    "encrypt_phone",
    "decrypt_phone",
    "generate_hmac",
]
