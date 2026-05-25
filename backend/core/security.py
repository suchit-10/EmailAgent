from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet, InvalidToken
from jose import jwt


class TokenCipher:
    def __init__(self, key: str):
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt token") from exc


def create_session_token(user_id: str, secret: str, minutes: int = 60 * 24 * 7) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": user_id, "exp": expires_at}, secret, algorithm="HS256")


def decode_session_token(token: str, secret: str) -> str:
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    return str(payload["sub"])
