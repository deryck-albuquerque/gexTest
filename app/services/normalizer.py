import re


def normalize_email(email: str) -> tuple[str | None, bool]:
    if not email:
        return None, False

    email = email.strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        return email, False

    return email, True


def normalize_phone(phone: str) -> tuple[str | None, bool]:
    if not phone:
        return None, False

    phone = re.sub(r"[^\d+]", "", phone)

    if len(re.sub(r"\D", "", phone)) < 10:
        return phone, False

    if not phone.startswith("+"):
        phone = "+" + phone

    return phone, True


def normalize_name(name: str | None) -> str:
    if not name:
        return "Customer"
    return name.strip()