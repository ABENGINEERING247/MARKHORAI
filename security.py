import hashlib, hmac, secrets, re

ITERATIONS = 310_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt_hex, expected = encoded.split("$")
        if scheme != "pbkdf2_sha256": return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except Exception: return False

def valid_username(value): return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", value or ""))
def valid_email(value): return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value or ""))
