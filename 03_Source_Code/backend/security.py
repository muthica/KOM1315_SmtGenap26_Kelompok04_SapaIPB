import base64
import hashlib
import json
import jwt
import os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeDecorator, String as SAString
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from backend import models

load_dotenv()

class EncryptedString(TypeDecorator):
    impl = SAString
    cache_ok = True

    def __init__(self, length=255, **kwargs):
        secret = os.getenv("FERNET_KEY") or os.getenv("SECRET_KEY")
        if not secret:
            raise ValueError("FERNET_KEY atau SECRET_KEY harus disetel untuk EncryptedString")

        key_material = secret.encode() if isinstance(secret, str) else secret
        key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
        self.fernet = Fernet(key)
        super().__init__(length=length, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError("EncryptedString hanya mendukung nilai string")

        import time
        start_time = time.perf_counter()
        hasil = self.fernet.encrypt(value.encode()).decode()
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (AES)] Penyimpanan Data PII Mahasiswa memakan {elapsed_time:.4f} ms")
        return hasil

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        import time
        start_time = time.perf_counter()
        try:
            hasil = self.fernet.decrypt(value.encode()).decode()
        except Exception:
            hasil = value
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (AES)] Pembacaan Data PII Mahasiswa memakan {elapsed_time:.4f} ms")
        return hasil

class SecurityService:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = "HS256"
        self.expire_minutes = 180

        if not self.secret_key:
            raise ValueError("SECRET_KEY tidak ditemukan. Pastikan file .env sudah ada")

    def buat_token_akses(self, data: dict) -> str:
        import time
        start_time = time.perf_counter()

        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Authentication] Pembuatan JWT Token memakan {elapsed_time:.4f} ms")
        return encoded_jwt

    def verifikasi_token(self, token: str) -> dict:
        import time
        start_time = time.perf_counter()
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authentication] Verifikasi JWT Token memakan {elapsed_time:.4f} ms")
            return {"status": "success", "data": payload}

        except jwt.ExpiredSignatureError:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authentication] Verifikasi JWT Token (GAGAL - Expired) memakan {elapsed_time:.4f} ms")
            return {"status": "error", "message": "Session timeout, silakan login ulang."}

        except jwt.InvalidTokenError:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authentication] Verifikasi JWT Token (GAGAL - Invalid) memakan {elapsed_time:.4f} ms")
            return {"status": "error", "message": "Token tidak valid. Unauthorized."}

    def ekstrak_token(self, request: Request) -> dict:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan. Harap login terlebih dahulu.")

        token = auth_header.split(" ")[1]
        user_info = self.verifikasi_token(token)

        if user_info["status"] == "error":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=user_info["message"])
        return user_info["data"]

    def cek_role(self, user_data: dict, db, request, *roles_diizinkan):
        import time
        start_time = time.perf_counter()

        role_user = user_data.get("role", "Guest")

        if role_user not in roles_diizinkan:
            url_target = request.url.path
            self.log_aktivitas(
                db=db,
                aksi=f"Akses terlarang ke {url_target} (Butuh: {', '.join(roles_diizinkan)})",
                request=request,
                status_log="Failed (RBAC - Forbidden)"
            )

            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authorization] Pengecekan Hak Akses (RBAC) (Ditolak) memakan {elapsed_time:.4f} ms")

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Akses ditolak. Fitur ini hanya untuk {', '.join(roles_diizinkan)}.")

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Authorization] Pengecekan Hak Akses (RBAC) memakan {elapsed_time:.4f} ms")

    def cek_kepemilikan_tiket(self, user_email: str, ticket_owner_email: str, user_role: str, id_tiket: str, request: Request, db):
        import time
        start_time = time.perf_counter()

        if user_role in ["staff", "admin"]:
            self.log_aktivitas(db=db, aksi=f"Akses tiket {id_tiket} oleh {user_role}", request=request, email=user_email, role=user_role, status_log="Success (OBAC)")
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authorization] Pengecekan Kepemilikan (OBAC) memakan {elapsed_time:.4f} ms")
            return True

        if user_email != ticket_owner_email:
            self.log_aktivitas(db=db, aksi=f"Akses Ilegal: {user_email} mencoba membuka tiket {id_tiket} milik {ticket_owner_email}", request=request, email=user_email, role=user_role, status_log="Failed (OBAC - Unauthorized)")
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Authorization] Pengecekan Kepemilikan (OBAC) (Ditolak) memakan {elapsed_time:.4f} ms")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak! Ini bukan tiket milik Anda.")

        self.log_aktivitas(db=db, aksi=f"Akses tiket {id_tiket} miliknya sendiri", request=request, email=user_email, role=user_role, status_log="Success (OBAC)")
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Authorization] Pengecekan Kepemilikan (OBAC) memakan {elapsed_time:.4f} ms")
        return True

    def log_aktivitas(self, db, aksi: str, request=None, email: str = None, role: str = None, status_log: str = "Success", ip_address: str = None):
        import time
        start_time = time.perf_counter()

        if not ip_address and request:
            ip_address = request.client.host
        elif not ip_address:
            ip_address = "Unknown IP"

        if not email or not role:
            try:
                if request:
                    user_data = self.ekstrak_token(request)
                    email = email or user_data.get("email", "Unknown")
                    role = role or user_data.get("role", "Guest")
            except Exception:
                pass

            email = email or "Unknown"
            role = role or "Guest"

        waktu_jkt = datetime.now(ZoneInfo("Asia/Jakarta"))
        new_log = models.AuditLog(
            waktu=waktu_jkt,
            email_aktor=email,
            role_aktor=role,
            aksi=aksi,
            status=status_log,
            ip_address=ip_address
        )
        db.add(new_log)
        db.commit()

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Accounting] Pencatatan Aktivitas (Audit Log) memakan {elapsed_time:.4f} ms")

    @staticmethod
    def buat_pasangan_kunci():
        import time
        start_time = time.perf_counter()

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        pem_private = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
        pem_public = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (RSA)] Pembangkitan Pasangan Kunci (2048-bit) memakan {elapsed_time:.4f} ms")

        return pem_private.decode('utf-8'), pem_public.decode('utf-8')

    @staticmethod
    def _get_fernet_from_passphrase(passphrase: str) -> Fernet:
        import time
        start_time = time.perf_counter()

        salt = b'sapa_ipb_secret_salt_2026'
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (AES)] Konversi Passphrase ke Kunci memakan {elapsed_time:.4f} ms")

        return Fernet(key)

    def bungkus_kunci_privat(self, pem_privat: str, passphrase: str) -> str:
        f = self._get_fernet_from_passphrase(passphrase)

        import time
        start_time = time.perf_counter()
        hasil = f.encrypt(pem_privat.encode()).decode()
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (AES)] Enkripsi Kunci Privat memakan {elapsed_time:.4f} ms")

        return hasil

    def buka_bungkus_kunci_privat(self, kunci_terenkripsi: str, passphrase: str) -> bytes:
        try:
            f = self._get_fernet_from_passphrase(passphrase)

            import time
            start_time = time.perf_counter()
            hasil = f.decrypt(kunci_terenkripsi.encode())
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Kriptografi (AES)] Dekripsi Kunci Privat memakan {elapsed_time:.4f} ms")

            return hasil
        except Exception:
            raise ValueError("Passphrase salah! Gagal membuka kunci.")

    def buat_digital_signature(self, payload: str, private_key_pem: bytes) -> str:
        import time
        start_time = time.perf_counter()

        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        signature = private_key.sign(payload.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())

        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"📊 [LEVEL 3 - Kriptografi (RSA)] Pembuatan Tanda Tangan Digital (RSA-PSS) memakan {elapsed_time:.4f} ms")

        return base64.b64encode(signature).decode('utf-8')

    def verifikasi_digital_signature(self, payload: str, signature_b64: str, public_key_pem: str) -> bool:
        import time
        start_time = time.perf_counter()

        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
            signature_bytes = base64.b64decode(signature_b64)
            public_key.verify(signature_bytes, payload.encode('utf-8'), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())

            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Kriptografi (RSA)] Verifikasi Tanda Tangan Digital (RSA-PSS) memakan {elapsed_time:.4f} ms")

            return True
        except Exception:
            elapsed_time = (time.perf_counter() - start_time) * 1000
            print(f"📊 [LEVEL 3 - Kriptografi (RSA)] Verifikasi Tanda Tangan Digital (RSA-PSS) (GAGAL) memakan {elapsed_time:.4f} ms")
            return False

sec_helper = SecurityService()
