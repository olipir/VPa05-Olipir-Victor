import os
from cryptography.fernet import Fernet


KEY_FILE = ".key"


def _get_key_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), KEY_FILE)


def key_exists():
    return os.path.exists(_get_key_path())


def generate_key():
    key = Fernet.generate_key()
    with open(_get_key_path(), "wb") as f:
        f.write(key)
    return key


def load_key():
    with open(_get_key_path(), "rb") as f:
        return f.read()


def encrypt_password(password: str) -> bytes:
    if not key_exists():
        key = generate_key()
    else:
        key = load_key()
    f = Fernet(key)
    return f.encrypt(password.encode())


def decrypt_password(token: bytes) -> str:
    key = load_key()
    f = Fernet(key)
    return f.decrypt(token).decode()
