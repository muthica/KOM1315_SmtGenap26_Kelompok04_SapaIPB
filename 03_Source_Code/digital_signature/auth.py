import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

from backend.database import get_db
from backend import models
from aaa_security.backend.security import sec_helper

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

class GoogleLoginPayload(BaseModel):
    google_id_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    role: str
    email: str
    nama_lengkap: str

class GoogleAuthService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not self.client_id:
            print("⚠️ WARNING: GOOGLE_CLIENT_ID tidak ditemukan di .env!")

        self.admin_emails = os.getenv("ADMIN_EMAILS", "").split(",") if os.getenv("ADMIN_EMAILS") else []
        self.staff_emails = os.getenv("STAFF_EMAILS", "").split(",") if os.getenv("STAFF_EMAILS") else []
        self.admin_emails = [e.strip() for e in self.admin_emails if e.strip()]
        self.staff_emails = [e.strip() for e in self.staff_emails if e.strip()]

    def verifikasi_google(self, token: str):
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), self.client_id)
            return idinfo.get("email"), idinfo.get("name")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Google tidak valid.")

    def kelola_user_db(self, db: Session, email: str, nama: str):
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if user:
                return user

            if email in self.admin_emails:
                new_user = models.AdminSistem(email=email, nama_lengkap=nama, role="admin", nip="00000000")
            elif email in self.staff_emails:
                new_user = models.StaffAkademik(email=email, nama_lengkap=nama, role="staff", nip="11111111")
            else:
                new_user = models.Mahasiswa(email=email, nama_lengkap=nama, role="mahasiswa")

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal membuat user di database: {str(e)}")


auth_helper = GoogleAuthService()

@router.post("/login", response_model=TokenResponse)
def login(payload: GoogleLoginPayload, request: Request, db: Session = Depends(get_db)):
    try:
        email_google, nama_google = auth_helper.verifikasi_google(payload.google_id_token)
    except HTTPException:
        sec_helper.log_aktivitas(db=db, aksi="Login via Google", request=request, email="Unknown", role="Guest", status_log="Failed (Invalid Token)")
        raise HTTPException(status_code=401, detail="Token Google tidak valid.")

    if not email_google.endswith("@apps.ipb.ac.id"):
        sec_helper.log_aktivitas(db=db, aksi="Login via Google", request=request, email=email_google, role="Guest", status_log="Failed (Non-IPB Email)")
        raise HTTPException(status_code=403, detail="Hanya email kampus yang diizinkan.")

    user = auth_helper.kelola_user_db(db, email_google, nama_google)

    if not user.is_active:
        sec_helper.log_aktivitas(db=db, aksi="Login via Google", request=request, email=email_google, role=user.role, status_log="Failed (Account Disabled)")
        raise HTTPException(status_code=403, detail="Akun Anda telah dinonaktifkan.")

    token = sec_helper.buat_token_akses({"email": user.email, "nama_lengkap": user.nama_lengkap, "role": user.role})
    sec_helper.log_aktivitas(db=db, aksi="Login via Google", request=request, email=user.email, role=user.role, status_log="Success")

    return TokenResponse(access_token=token, role=user.role, email=user.email, nama_lengkap=user.nama_lengkap)

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    sec_helper.log_aktivitas(db=db, aksi="Logout", request=request, status_log="Success")
    return {"message": "Logout berhasil."}
