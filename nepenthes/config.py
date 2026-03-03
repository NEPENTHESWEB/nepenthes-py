"""YAML configuration loader with environment variable overrides."""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SiloConfig:
    name: str
    corpus: str
    wordlist: str
    template: str = "default"
    min_wait: Optional[float] = None
    max_wait: Optional[float] = None
    header_wait_min: float = 5.0
    header_wait_max: float = 30.0
    default: bool = False
    prefixes: list[str] = field(default_factory=list)
    zero_delay: bool = False
    redirect_rate: int = 0
    bogon_filter: bool = True


@dataclass
class AppConfig:
    http_host: str = "localhost"
    http_port: int = 8893
    unix_socket: Optional[str] = None
    templates: list[str] = field(default_factory=lambda: ["templates"])
    seed_file: Optional[str] = None
    min_wait: float = 10.0
    max_wait: float = 65.0
    detach: bool = False
    log_level: str = "info"
    pidfile: Optional[str] = None
    real_ip_header: str = "X-Forwarded-For"
    silo_header: str = "X-Silo"
    stats_remember_time: int = 3600
    silos: list[SiloConfig] = field(default_factory=list)

    def get_default_silo(self) -> SiloConfig:
        for silo in self.silos:
            if silo.default:
                return silo
        return self.silos[0]

    def get_silo_by_name(self, name: str) -> Optional[SiloConfig]:
        for silo in self.silos:
            if silo.name == name:
                return silo
        return None


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw = _apply_env_overrides(raw)

    silos = []
    for s in raw.get("silos", []):
        silos.append(SiloConfig(
            name=s["name"],
            corpus=s["corpus"],
            wordlist=s["wordlist"],
            template=s.get("template", "default"),
            min_wait=s.get("min_wait"),
            max_wait=s.get("max_wait"),
            header_wait_min=s.get("header_wait_min", 5.0),
            header_wait_max=s.get("header_wait_max", 30.0),
            default=s.get("default", False),
            prefixes=s.get("prefixes", []),
            zero_delay=s.get("zero_delay", False),
            redirect_rate=s.get("redirect_rate", 0),
            bogon_filter=s.get("bogon_filter", True),
        ))

    if not silos:
        raise ValueError("At least one silo must be defined in configuration")

    defaults_count = sum(1 for s in silos if s.default)
    if defaults_count > 1:
        raise ValueError("Only one silo can be marked as default")

    return AppConfig(
        http_host=raw.get("http_host", "localhost"),
        http_port=int(raw.get("http_port", 8893)),
        unix_socket=raw.get("unix_socket"),
        templates=raw.get("templates", ["templates"]),
        seed_file=raw.get("seed_file"),
        min_wait=float(raw.get("min_wait", 10.0)),
        max_wait=float(raw.get("max_wait", 65.0)),
        detach=raw.get("detach", False),
        log_level=raw.get("log_level", "info"),
        pidfile=raw.get("pidfile"),
        real_ip_header=raw.get("real_ip_header", "X-Forwarded-For"),
        silo_header=raw.get("silo_header", "X-Silo"),
        stats_remember_time=int(raw.get("stats_remember_time", 3600)),
        silos=silos,
    )


ENV_MAP = {
    "NEPENTHES_HOST": "http_host",
    "NEPENTHES_PORT": "http_port",
    "NEPENTHES_MIN_WAIT": "min_wait",
    "NEPENTHES_MAX_WAIT": "max_wait",
    "NEPENTHES_LOG_LEVEL": "log_level",
    "NEPENTHES_SEED_FILE": "seed_file",
}


def _apply_env_overrides(raw: dict) -> dict:
    for env_key, config_key in ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            raw[config_key] = val
    return raw
