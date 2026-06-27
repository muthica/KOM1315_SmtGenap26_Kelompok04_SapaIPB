import hashlib
import hmac
import secrets


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if not password:
        raise ValueError("Password tidak boleh kosong")

    salt_bytes = salt.encode("utf-8") if salt else secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    return derived_key.hex(), salt_bytes.hex()


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    if not password or not stored_hash or not salt_hex:
        return False

    salt_bytes = bytes.fromhex(salt_hex)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    return hmac.compare_digest(derived_key.hex(), stored_hash)
