import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

def gen_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_code(code: str, salt: str) -> str:
    return hashlib.sha256((salt + ":" + code).encode()).hexdigest()

def verify_code(code: str, code_hash: str, salt: str) -> bool:
    calc = hash_code(code, salt)
    return hmac.compare_digest(calc, code_hash)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def expires_in(minutes: int) -> datetime:
    return utcnow() + timedelta(minutes=minutes)
