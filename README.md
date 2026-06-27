# 🔐 SAPA IPB — Security Documentation

SAPA IPB adalah sistem layanan akademik yang juga memiliki mekanisme keamanan terintegrasi untuk melindungi data pengguna, proses tiket, dan aktivitas administratif.

---

## 👥 Tim Security & Implementasi

| Nama | Peran |
|------|-------|
| Fadia Syakira Mustaniroh | Security Engineer / Digital Signature & Key Management |
| Muthia Khansa | Database Security Engineer / Implementasi Hashing pada Model Database |
| Indriyani Khairan Nisa | Security QA / Testing dan Log Keamanan |

*Dokumen luaran dikerjakan secara bersama - sama sekelompok
---

## 🛡️ Fokus Keamanan

Sistem ini telah menerapkan beberapa mekanisme keamanan penting, di antaranya:

- Autentikasi berbasis Google SSO untuk akun IPB
- JWT untuk akses pengguna yang terotentikasi
- Enkripsi data sensitif menggunakan kriptografi simetris
- Penggunaan kunci publik dan kunci privat untuk digital signature
- Penyimpanan log aktivitas untuk audit dan monitoring
- Perlindungan data pada model database melalui hashing dan salting

---

## 📁 Struktur Keamanan yang Dipakai

Secara ringkas, bagian keamanan sistem ditempatkan dalam folder berikut:

- [aaa_security/backend](aaa_security/backend) — bagian kriptografi, enkripsi/dekripsi, dan pengelolaan kunci
- [aaa_security/database](aaa_security/database) — skema database, hashing, dan perlindungan data model
- [aaa_security/digital_signature](aaa_security/digital_signature) — autentikasi, JWT, serta digital signature dan non-repudiation

---
# 🔄 Alur Penggunaan Sistem

## 🔹 Alur Pengguna (Mahasiswa)
1. **Login:** Mahasiswa masuk ke aplikasi menggunakan akun Google institusi IPB.
2. **Buat Tiket:** Mahasiswa mengisi formulir pengajuan, memilih kategori layanan, menulis deskripsi, dan mengunggah dokumen pendukung.
3. **Masuk Antrean:** Tiket otomatis tersimpan ke database dan masuk ke dalam daftar antrean staf akademik.
4. **Pantau Status:** Mahasiswa mendapatkan notifikasi berkala di dashboard setiap kali staf memperbarui status pengerjaan tiket.
5. **Tiket Selesai:** Tiket dinyatakan ditutup (*Closed*) setelah staf menyelesaikan permohonan dan memberikan hasil layanan.

---

## 🔹 Alur Staf Akademik
1. **Masuk Dashboard:** Staf login ke sistem menggunakan akun khusus staf.
2. **Cek Antrean:** Staf meninjau daftar dokumen tiket masuk dari mahasiswa yang statusnya masih baru (*Open*).
3. **Validasi & Beri Respon:** Staf memeriksa kelayakan dokumen mahasiswa, memproses permohonan, dan memberikan tanggapan disertai digital signature.
4. **Selesaikan Tiket:** Staf mengubah status tiket menjadi selesai (*Closed*), dan sistem otomatis memicu notifikasi selesai ke halaman mahasiswa.

---

## 🔹 Alur Admin
1. **Login Admin:** Admin masuk ke sistem melalui halaman dashboard khusus administrator.
2. **Kelola Pengguna:** Admin memantau daftar pengguna aktif, mendaftarkan staf baru, atau menonaktifkan akun jika diperlukan.
3. **Sinkronisasi Data:** Admin memicu proses sinkronisasi berkas panduan akademik terbaru agar AI Chatbot selalu memperbarui basis pengetahuannya.
4. **Meninjau Log Keamanan:** Admin meninjau dan memantau dashboard yang berisi log keamanan agar segera mengetahui jika ada upaya percobaan penyerangan sistem.

---

# 🏗️ Arsitektur Sistem

Aplikasi SAPA IPB dibangun menggunakan arsitektur modern berbasis pemisahan penuh (*Decoupled Architecture*):

* **Frontend Layer (React.js):** Bertanggung jawab atas visualisasi antarmuka pengguna, manajemen status aplikasi di sisi klien, dan penanganan interaksi form pengajuan. Di-deploy menggunakan platform **Vercel**.
* **Backend Layer (FastAPI):** Bertindak sebagai *core engine* penyedia RESTful API yang mengelola logika bisnis autentikasi, manajemen status tiket, sistem notifikasi, dan pengelolaan basis pengetahuan. Di-deploy menggunakan platform **Railway**.
* **Database Layer (PostgreSQL):** Berfungsi sebagai tempat penyimpanan data relasional yang persisten untuk data pengguna, informasi tiket, dan log sistem.
* **AI Engine Layer (RAG Chatbot):** Modul kecerdasan buatan yang terintegrasi dengan Large Language Model (LLM) dan pangkalan data vektor untuk menyajikan layanan tanya-jawab akademik otomatis berbasis dokumen panduan IPB.

```
Frontend (React + Vite)
          │
          ▼
 Backend API (FastAPI)
          │
          ▼
 PostgreSQL Database
```

---

# 🛠️ Tech Stack

## Frontend

- React
- Vite
- Tailwind CSS
- React Router

## Backend

- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- JWT Authentication

## Database

- PostgreSQL

## Deployment

- Vercel (Frontend)
- Railway (Backend, Database)

---

# 📌 Modul Sistem

- Authentication & Authorization
- Ticket Management
- Knowledge Base Management
- Chatbot SAPA
- Notification System
- User Management
- Security Key Management
- Dashboard Monitoring

---

# 🖇️ Deployment Links

- Frontend: https://sapa-ipb.vercel.app/
- Backend: https://sapa-ipb-production.up.railway.app

---

# 📚 Mata Kuliah

Keamanan Informasi (KI)

Departemen Ilmu Komputer  
Sekolah Sains Data, Matematika, dan Informatika  
IPB University



