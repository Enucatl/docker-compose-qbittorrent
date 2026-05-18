import ipaddress
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_qbittorrent_config as config


def test_auth_subnet_uses_exact_host_prefixes() -> None:
    assert config.auth_subnet(ipaddress.ip_address("172.16.32.17")) == "172.16.32.17/32"
    assert (
        config.auth_subnet(ipaddress.ip_address("2a02:168:6278:a001::11"))
        == "2a02:168:6278:a001::11/128"
    )


def test_replace_or_append_replaces_existing_key() -> None:
    lines = [
        "[Preferences]\n",
        "WebUI\\AuthSubnetWhitelist=172.16.0.0/16\n",
        "WebUI\\LocalHostAuth=false\n",
    ]

    assert config.replace_or_append(
        lines, "WebUI\\AuthSubnetWhitelist", "172.16.32.17/32"
    ) == [
        "[Preferences]\n",
        "WebUI\\AuthSubnetWhitelist=172.16.32.17/32\n",
        "WebUI\\LocalHostAuth=false\n",
    ]


def test_replace_or_append_appends_missing_key() -> None:
    lines = ["[Preferences]\n", "WebUI\\LocalHostAuth=false\n"]

    assert config.replace_or_append(
        lines, "WebUI\\TrustedReverseProxiesList", "172.16.32.17"
    ) == [
        "[Preferences]\n",
        "WebUI\\LocalHostAuth=false\n",
        "WebUI\\TrustedReverseProxiesList=172.16.32.17\n",
    ]


def test_main_writes_resolved_traefik_ips_and_removes_stale_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_config = tmp_path / "source.conf"
    target_config = tmp_path / "qBittorrent.conf"
    target_config_tmp = tmp_path / "qBittorrent.conf.tmp"
    stale_generated_config = tmp_path / "qBittorrent_new.conf"
    source_config.write_text(
        "\n".join(
            [
                "[Preferences]",
                "WebUI\\AuthSubnetWhitelist=",
                "WebUI\\TrustedReverseProxiesList=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    stale_generated_config.write_text("stale", encoding="utf-8")

    monkeypatch.setattr(config, "SOURCE_CONFIG", source_config)
    monkeypatch.setattr(config, "TARGET_CONFIG", target_config)
    monkeypatch.setattr(config, "TARGET_CONFIG_TMP", target_config_tmp)
    monkeypatch.setattr(config, "STALE_GENERATED_CONFIG", stale_generated_config)
    monkeypatch.setattr(
        config,
        "resolve_ips",
        lambda hostname: [
            ipaddress.ip_address("172.16.32.17"),
            ipaddress.ip_address("2a02:168:6278:a001::11"),
        ],
    )

    config.main()

    assert (
        "WebUI\\AuthSubnetWhitelist=172.16.32.17/32,2a02:168:6278:a001::11/128"
        in target_config.read_text(encoding="utf-8")
    )
    assert (
        "WebUI\\TrustedReverseProxiesList=172.16.32.17,2a02:168:6278:a001::11"
        in target_config.read_text(encoding="utf-8")
    )
    assert not stale_generated_config.exists()
