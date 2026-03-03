"""Rolling statistics buffer with API endpoints."""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HitRecord:
    address: str
    agent: str
    uri: str
    silo: str
    response: int
    bytes_generated: int
    bytes_sent: int
    delay: float
    cpu: float
    complete: bool
    when: float
    hit_id: str
    bogon: bool = False
    redirect: bool = False


class StatsCollector:
    def __init__(self, remember_time: int = 3600):
        self._buffer: list[HitRecord] = []
        self._lock = threading.Lock()
        self._remember_time = remember_time
        self._counter = 0
        self._start_time = time.monotonic()

        self._hits_total = 0
        self._bytes_generated_total = 0
        self._bytes_sent_total = 0
        self._delay_total = 0.0
        self._cpu_total = 0.0

    def record_hit(self, address: str, agent: str, uri: str, silo: str,
                   response: int, bytes_generated: int, bytes_sent: int,
                   delay: float, cpu: float, complete: bool,
                   bogon: bool = False, redirect: bool = False):
        with self._lock:
            self._counter += 1
            hit_id = f"{int(time.time())}.{self._counter}"
            record = HitRecord(
                address=address, agent=agent, uri=uri, silo=silo,
                response=response, bytes_generated=bytes_generated,
                bytes_sent=bytes_sent, delay=delay, cpu=cpu,
                complete=complete, when=time.monotonic(),
                hit_id=hit_id, bogon=bogon, redirect=redirect,
            )
            self._buffer.append(record)

            self._hits_total += 1
            self._bytes_generated_total += bytes_generated
            self._bytes_sent_total += bytes_sent
            self._delay_total += delay
            self._cpu_total += cpu

    def _prune(self) -> list[HitRecord]:
        cutoff = time.monotonic() - self._remember_time
        self._buffer = [r for r in self._buffer if r.when >= cutoff]
        return self._buffer

    def get_overview(self, silo: Optional[str] = None) -> dict:
        with self._lock:
            records = self._prune()
            if silo:
                records = [r for r in records if r.silo == silo]

            addresses = set()
            agents = set()
            total_delay = 0.0
            total_cpu = 0.0
            total_bytes_sent = 0
            total_bytes_generated = 0
            bogons = 0
            redirects = 0
            active = 0

            for r in records:
                addresses.add(r.address)
                agents.add(r.agent)
                total_delay += r.delay
                total_cpu += r.cpu
                total_bytes_sent += r.bytes_sent
                total_bytes_generated += r.bytes_generated
                if r.bogon:
                    bogons += 1
                if r.redirect:
                    redirects += 1
                if not r.complete:
                    active += 1

            unsent = total_bytes_generated - total_bytes_sent
            unsent_pct = (unsent / total_bytes_generated * 100) if total_bytes_generated > 0 else 0.0
            uptime = time.monotonic() - self._start_time
            cpu_pct = (total_cpu / uptime * 100) if uptime > 0 else 0.0

            return {
                "hits": len(records),
                "addresses": len(addresses),
                "agents": len(agents),
                "bytes_sent": total_bytes_sent,
                "bytes_generated": total_bytes_generated,
                "delay": round(total_delay, 3),
                "cpu": round(total_cpu, 6),
                "cpu_percent": round(cpu_pct, 6),
                "active": active,
                "unsent_bytes": unsent,
                "unsent_bytes_percent": round(unsent_pct, 6),
                "bogons": bogons,
                "redirects": redirects,
                "uptime": round(uptime),
                "hits_total": self._hits_total,
                "bytes_generated_total": self._bytes_generated_total,
                "bytes_sent_total": self._bytes_sent_total,
                "delay_total": round(self._delay_total, 6),
                "cpu_total": round(self._cpu_total, 2),
                "memory_usage": 0,
            }

    def get_agents(self, silo: Optional[str] = None) -> dict:
        with self._lock:
            records = self._prune()
            if silo:
                records = [r for r in records if r.silo == silo]
            counts: dict[str, int] = defaultdict(int)
            for r in records:
                counts[r.agent] += 1
            return dict(counts)

    def get_addresses(self, silo: Optional[str] = None) -> dict:
        with self._lock:
            records = self._prune()
            if silo:
                records = [r for r in records if r.silo == silo]
            counts: dict[str, int] = defaultdict(int)
            for r in records:
                counts[r.address] += 1
            return dict(counts)

    def get_buffer(self, from_id: Optional[str] = None, silo: Optional[str] = None) -> list[dict]:
        with self._lock:
            records = self._prune()
            if silo:
                records = [r for r in records if r.silo == silo]

            if from_id:
                found = False
                filtered = []
                for r in records:
                    if found:
                        filtered.append(r)
                    elif r.hit_id == from_id:
                        found = True
                records = filtered

            return [
                {
                    "address": r.address,
                    "agent": r.agent,
                    "uri": r.uri,
                    "silo": r.silo,
                    "response": r.response,
                    "bytes_generated": r.bytes_generated,
                    "bytes_sent": r.bytes_sent,
                    "delay": round(r.delay, 6),
                    "cpu": round(r.cpu, 6),
                    "complete": r.complete,
                    "when": round(r.when, 6),
                    "id": r.hit_id,
                }
                for r in records
            ]
