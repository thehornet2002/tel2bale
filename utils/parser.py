from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from urllib.parse import urlparse, urlunparse


_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "broadcasthost",
}

_BLOCKED_SUFFIXES = (
    ".localhost",
    ".localdomain",
    ".local",
    ".lan",
    ".home",
    ".internal",
    ".intranet",
)

_ALLOWED_SCHEMES = {"https"}


async def validate_link(s: str):
    """
    اعتبارسنجی سخت‌گیرانه برای URLهای عمومی، مخصوصاً S3 endpoint.

    خروجی:
        str   لینک نرمال‌شده و امن
        False لینک نامعتبر یا مشکوک

    این تابع عمداً localhost، loopback، IPهای private/internal/reserved/link-local،
    دامنه‌های محلی مثل *.local و دامنه‌هایی که به IP داخلی resolve شوند را رد می‌کند.
    """
    return await validate_public_https_url(s, resolve_dns=True)


async def validate_public_https_url(
    value: str,
    *,
    resolve_dns: bool = True,
    dns_timeout: float = 3.0,
):
    if not value or not isinstance(value, str):
        return False

    value = value.strip()

    if not value:
        return False

    # جلوگیری از URLهایی که space یا newline دارند
    if any(ch.isspace() for ch in value):
        return False

    # جلوگیری از کاراکترهای کنترلی
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False

    # اگر scheme ندارد، فقط https اضافه می‌کنیم.
    # عمداً http را پیش‌فرض نمی‌گذاریم.
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value

    parsed = urlparse(value)

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return False

    # URLهایی مثل https://user:pass@example.com مجاز نیستند.
    if parsed.username or parsed.password:
        return False

    if not parsed.hostname:
        return False

    host = _normalize_hostname(parsed.hostname)
    if not host:
        return False

    if _is_blocked_host_without_dns(host):
        return False

    if resolve_dns:
        ok = await _resolves_only_to_public_ips(
            host=host,
            port=parsed.port,
            timeout=dns_timeout,
        )
        if not ok:
            return False

    netloc = host

    if parsed.port is not None:
        if parsed.port < 1 or parsed.port > 65535:
            return False

        netloc = f"{host}:{parsed.port}"

    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            netloc,
            parsed.path or "",
            "",
            parsed.query or "",
            "",
        )
    )

    return normalized


def _normalize_hostname(hostname: str) -> str | None:
    try:
        host = hostname.strip().strip("[]").rstrip(".").lower()

        if not host:
            return None

        # پشتیبانی امن‌تر از دامنه‌های unicode با تبدیل به IDNA
        return host.encode("idna").decode("ascii").lower()

    except Exception:
        return None


def _is_blocked_host_without_dns(host: str) -> bool:
    labels = host.split(".")

    if host in _BLOCKED_HOSTNAMES:
        return True

    # مثل api.localhost.example را هم مشکوک می‌گیریم
    if "localhost" in labels:
        return True

    if host.endswith(_BLOCKED_SUFFIXES):
        return True

    # IP مستقیم، IPv4 یا IPv6
    if _is_blocked_ip_literal(host):
        return True

    # فرم‌های عددی/hex/octal مثل:
    # 2130706433
    # 017700000001
    # 0x7f000001
    if _looks_like_numeric_ip_obfuscation(host):
        return True

    # دامنه‌هایی مثل:
    # 127.0.0.1.nip.io
    # 192.168.1.10.sslip.io
    if _contains_blocked_ipv4_labels(labels):
        return True

    return False


def _is_blocked_ip_literal(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False

    return _is_unsafe_ip(ip)


def _is_unsafe_ip(ip: ipaddress._BaseAddress) -> bool:
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_multicast,
            ip.is_unspecified,
        )
    )


def _looks_like_numeric_ip_obfuscation(host: str) -> bool:
    # 2130706433
    # 017700000001
    # 0x7f000001
    if re.fullmatch(r"(?:0x[0-9a-f]+|0[0-7]+|\d+)", host, re.IGNORECASE):
        return True

    # 0x7f.0.0.1
    # 0177.0.0.1
    # شکل‌های مشابه
    if re.fullmatch(
        r"(?:0x[0-9a-f]+|0[0-7]+|\d+)(?:\.(?:0x[0-9a-f]+|0[0-7]+|\d+)){1,3}",
        host,
        re.IGNORECASE,
    ):
        return True

    return False


def _contains_blocked_ipv4_labels(labels: list[str]) -> bool:
    """
    برای تشخیص دامنه‌هایی که IP را داخل labelهایشان پنهان می‌کنند.

    مثال:
        127.0.0.1.nip.io
        192.168.1.5.sslip.io
    """
    for i in range(0, max(0, len(labels) - 3)):
        chunk = labels[i : i + 4]

        if not all(part.isdigit() for part in chunk):
            continue

        candidate = ".".join(chunk)

        try:
            ip = ipaddress.ip_address(candidate)
        except ValueError:
            continue

        if _is_unsafe_ip(ip):
            return True

    return False


async def _resolves_only_to_public_ips(
    host: str,
    port: int | None,
    timeout: float,
) -> bool:
    """
    DNS resolve می‌کند و مطمئن می‌شود همه IPهای برگشتی عمومی و امن هستند.

    اگر DNS fail شود، عمداً False برمی‌گردانیم تا endpoint مشکوک ذخیره نشود.
    """
    try:
        infos = await asyncio.wait_for(
            asyncio.to_thread(
                socket.getaddrinfo,
                host,
                port or 443,
                type=socket.SOCK_STREAM,
            ),
            timeout=timeout,
        )
    except Exception:
        return False

    resolved_ips: set[str] = set()

    for info in infos:
        sockaddr = info[4]

        if not sockaddr:
            return False

        ip_text = sockaddr[0]

        try:
            ip = ipaddress.ip_address(ip_text)
        except ValueError:
            return False

        resolved_ips.add(str(ip))

        if _is_unsafe_ip(ip):
            return False

    return bool(resolved_ips)