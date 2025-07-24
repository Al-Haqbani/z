import socket
from typing import List

COMMON_SUBS = ['direct', 'origin', 'real', 'server']

def discover_ip(domain: str) -> List[str]:
    ips = []
    try:
        ips.extend(socket.gethostbyname_ex(domain)[2])
    except Exception:
        pass
    for sub in COMMON_SUBS:
        host = f"{sub}.{domain}"
        try:
            ips.extend(socket.gethostbyname_ex(host)[2])
        except Exception:
            continue
    return list(set(ips))
