from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.security import EncryptedString
from datetime import datetime, timezone


def _now():
    """Waktu UTC sekarang — menggantikan datetime.utcnow() yang deprecated."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    email = Column(String, primary_key=True, index=True)
    nama_lengkap = Column(String, nullable=False)
    role = Column(String)
    tanggal_terdaftar = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": role,
    }

class Mahasiswa(User):
    __tablename__ = "mahasiswa"
    email = Column(String, ForeignKey("users.email"), primary_key=True)
    nim = Column(String, unique=True, nullable=True)
    program_studi = Column(String, nullable=True)
    departemen = Column(String, nullable=True)
    fakultas = Column(String, nullable=True)
    alamat = Column(EncryptedString(), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "mahasiswa"}

    tikets = relationship("TiketLayanan", back_populates="pengaju")
    chatbot_sessions = relationship("ChatbotSession", back_populates="mahasiswa")

class StaffAkademik(User):
    __tablename__ = "staff_akademik"
    email = Column(String, ForeignKey("users.email"), primary_key=True)
    nip = Column(String, unique=True, nullable=True)
    unit_kerja = Column(String, nullable=True)
    public_key = Column(Text, nullable=True)
    encrypted_private_key = Column(Text, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "staff"}

    tikets_diproses = relationship("TiketLayanan", back_populates="pemroses")
    dokumen_diupload = relationship("KnowledgeBase", foreign_keys="[KnowledgeBase.diupload_oleh]", back_populates="uploader")


class AdminSistem(User):
    __tablename__ = "admin_sistem"
    email = Column(String, ForeignKey("users.email"), primary_key=True)
    nip = Column(String, unique=True, nullable=True)
    __mapper_args__ = {"polymorphic_identity": "admin"}

    dokumen_disetujui = relationship("KnowledgeBase", foreign_keys="[KnowledgeBase.disetujui_oleh]", back_populates="approver")
    dokumen_ditolak = relationship("KnowledgeBase", foreign_keys="[KnowledgeBase.ditolak_oleh]", back_populates="rejecter")


class Layanan(Base):
    __tablename__ = "layanan"
    id_layanan = Column(String, primary_key=True)
    nama_layanan = Column(String)
    tipe_output = Column(String)
    unit_penanggung_jawab = Column(String)

    tikets = relationship("TiketLayanan", back_populates="layanan")


class TiketLayanan(Base):
    __tablename__ = "tiket_layanan"
    id_tiket = Column(String, primary_key=True)
    waktu_submit = Column(DateTime(timezone=True), default=_now)
    status = Column(String, default="Open")
    subjek = Column(String, nullable=False)
    kategori = Column(String, nullable=False)
    deskripsi = Column(Text, nullable=True)

    data_request = Column(JSONB, nullable=True)
    file_lampiran = Column(String, nullable=True)

    nim_pengaju = Column(String, nullable=True, index=True)
    program_studi_pengaju = Column(String, nullable=True)

    email_mahasiswa = Column(String, ForeignKey("mahasiswa.email"), nullable=True, index=True)
    email_staff = Column(String, ForeignKey("staff_akademik.email"), nullable=True)
    id_layanan = Column(String, ForeignKey("layanan.id_layanan"), nullable=True)

    pengaju = relationship("Mahasiswa", back_populates="tikets")
    pemroses = relationship("StaffAkademik", back_populates="tikets_diproses")
    layanan = relationship("Layanan", back_populates="tikets")
    notifikasi = relationship("Notifikasi", back_populates="tiket", cascade="all, delete-orphan")
    tanggapan = relationship("TanggapanStaff", back_populates="tiket", uselist=False, cascade="all, delete-orphan")


class TanggapanStaff(Base):
    __tablename__ = "tanggapan_staff"
    id_tanggapan = Column(String, primary_key=True)
    id_tiket = Column(String, ForeignKey("tiket_layanan.id_tiket"), unique=True)
    email_staff = Column(String, ForeignKey("staff_akademik.email"))
    pesan = Column(Text, nullable=False)
    file_output = Column(String, nullable=True)
    hash_lampiran = Column(String, nullable=True)
    waktu = Column(DateTime(timezone=True), default=_now)
    digital_signature = Column(Text, nullable=True)

    tiket = relationship("TiketLayanan", back_populates="tanggapan")


class Notifikasi(Base):
    __tablename__ = "notifikasi"
    id_notifikasi = Column(String, primary_key=True)
    pesan = Column(String)
    waktu = Column(DateTime(timezone=True), default=_now)
    is_read = Column(Boolean, default=False)
    id_tiket = Column(String, ForeignKey("tiket_layanan.id_tiket"), index=True)

    tiket = relationship("TiketLayanan", back_populates="notifikasi")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id_kb = Column(Integer, primary_key=True, index=True, autoincrement=True)
    judul = Column(String, index=True)
    kategori = Column(String)
    path = Column(String)
    filename = Column(String)
    status = Column(String, default="Pending")

    waktu_upload = Column(DateTime, default=datetime.now)
    diupload_oleh = Column(String, ForeignKey("staff_akademik.email"))

    waktu_setujui = Column(DateTime, nullable=True)
    disetujui_oleh = Column(String, ForeignKey("admin_sistem.email"), nullable=True)

    waktu_tolak = Column(DateTime, nullable=True)
    ditolak_oleh = Column(String, ForeignKey("admin_sistem.email"), nullable=True)

    uploader = relationship("StaffAkademik", foreign_keys=[diupload_oleh], back_populates="dokumen_diupload")
    approver = relationship("AdminSistem", foreign_keys=[disetujui_oleh], back_populates="dokumen_disetujui")
    rejecter = relationship("AdminSistem", foreign_keys=[ditolak_oleh], back_populates="dokumen_ditolak")

class ChatbotSession(Base):
    __tablename__ = "chatbot_sessions"
    id_chat = Column(String, primary_key=True)
    email_mahasiswa = Column(String, ForeignKey("mahasiswa.email"), index=True)
    pesan_user = Column(String)
    jawaban_bot = Column(Text, nullable=True)
    waktu_kirim = Column(DateTime(timezone=True), default=_now)

    mahasiswa = relationship("Mahasiswa", back_populates="chatbot_sessions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id_log = Column(Integer, primary_key=True, autoincrement=True)
    waktu = Column(DateTime(timezone=True), default=_now)
    email_aktor = Column(String, index=True)
    role_aktor = Column(String)
    aksi = Column(String)
    status = Column(String)
    ip_address = Column(String)
