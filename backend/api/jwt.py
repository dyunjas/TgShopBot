from datetime import datetime, timedelta, timezone
import jwt

def create_access_token(*, secret: str, admin_id: int, role: str, minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(admin_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")
