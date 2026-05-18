#!/usr/bin/env python3

import ipaddress
import shutil
import socket
from pathlib import Path


SOURCE_CONFIG = Path("/source/qBittorrent.conf")
TARGET_CONFIG = Path("/target/qBittorrent.conf")
TARGET_CONFIG_TMP = Path("/target/qBittorrent.conf.tmp")
STALE_GENERATED_CONFIG = Path("/target/qBittorrent_new.conf")
TRAEFIK_HOSTNAME = "traefik."


def resolve_ips(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    resolved: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
        if family not in {socket.AF_INET, socket.AF_INET6}:
            continue
        resolved.add(ipaddress.ip_address(sockaddr[0]))
    return sorted(resolved, key=lambda address: (address.version, int(address)))


def auth_subnet(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    prefix = 32 if address.version == 4 else 128
    return f"{address}/{prefix}"


def replace_or_append(lines: list[str], key: str, value: str) -> list[str]:
    replacement = f"{key}={value}\n"
    replaced = False
    output: list[str] = []

    for line in lines:
        if line.startswith(f"{key}="):
            output.append(replacement)
            replaced = True
        else:
            output.append(line)

    if not replaced:
        output.append(replacement)

    return output


def main() -> None:
    traefik_ips = resolve_ips(TRAEFIK_HOSTNAME)
    if not traefik_ips:
        raise RuntimeError(f"failed to resolve any IPs for {TRAEFIK_HOSTNAME}")

    shutil.copyfile(SOURCE_CONFIG, TARGET_CONFIG)

    lines = TARGET_CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    auth_subnets = ",".join(auth_subnet(address) for address in traefik_ips)
    trusted_proxies = ",".join(str(address) for address in traefik_ips)

    lines = replace_or_append(lines, "WebUI\\AuthSubnetWhitelist", auth_subnets)
    lines = replace_or_append(
        lines, "WebUI\\TrustedReverseProxiesList", trusted_proxies
    )

    TARGET_CONFIG_TMP.write_text("".join(lines), encoding="utf-8")
    TARGET_CONFIG_TMP.replace(TARGET_CONFIG)
    TARGET_CONFIG.chmod(0o644)
    STALE_GENERATED_CONFIG.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
