import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(key.encode()) if key else None

def encrypt_text(text: str) -> str:
    if not text or not cipher: return text
    return cipher.encrypt(text.encode()).decode()

def decrypt_text(text: str) -> str:
    if not text or not cipher: return text
    try:
        return cipher.decrypt(text.encode()).decode()
    except:
        return "[Encrypted Message]"