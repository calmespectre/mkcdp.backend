import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PHONE_RE = re.compile(r"^\+?[\d\s()\-]{7,20}$")

def normalize_phone(raw):
    if not raw:
        return ""
    s = re.sub(r"[\s()\-]", "", raw.strip())
    if s.startswith("0"):
        s = "+254" + s[1:]
    elif s.startswith("254") and not s.startswith("+"):
        s = "+" + s
    elif s.startswith("7") and len(s) == 9:
        s = "+254" + s
    elif s.startswith("1") and len(s) == 9:
        s = "+254" + s
    return s

def is_valid_kenyan_msisdn(phone):
    p = normalize_phone(phone)
    return bool(re.match(r"^\+254(7|1)\d{8}$", p))

def to_decimal(value, places="0.01"):
    try:
        return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")

def client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def reference(prefix):
    import secrets, string, time
    ts = str(int(time.time()))[-8:]
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{ts}{suffix}"