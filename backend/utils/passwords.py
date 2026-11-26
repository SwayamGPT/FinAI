import bcrypt

# bcrypt only uses the first 72 bytes; bcrypt>=5 raises instead of truncating.
_MAX_BYTES = 72


def _prep(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(password), hashed.encode("utf-8"))
    except ValueError:
        return False
