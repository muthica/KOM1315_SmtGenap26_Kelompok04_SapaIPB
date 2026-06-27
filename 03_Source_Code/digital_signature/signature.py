from aaa_security.backend.security import sec_helper


def buat_tanda_tangan(payload: str, private_key_pem: str) -> str:
    return sec_helper.buat_digital_signature(payload, private_key_pem.encode("utf-8"))


def verifikasi_tanda_tangan(payload: str, signature_b64: str, public_key_pem: str) -> bool:
    return sec_helper.verifikasi_digital_signature(payload, signature_b64, public_key_pem)
