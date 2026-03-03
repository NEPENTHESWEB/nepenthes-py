"""Async HTTP server with drip-feed response logic."""

import asyncio
import hashlib
import logging
import random
import time
from typing import Optional

from aiohttp import web

from .config import AppConfig, SiloConfig
from .silos import SiloManager
from .stats import StatsCollector

logger = logging.getLogger("nepenthes")


class TarpitServer:
    def __init__(self, config: AppConfig, silo_manager: SiloManager, stats: StatsCollector):
        self.config = config
        self.silo_manager = silo_manager
        self.stats = stats
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_route("GET", "/stats", self._handle_stats)
        self.app.router.add_route("GET", "/stats/agents", self._handle_stats_agents)
        self.app.router.add_route("GET", "/stats/addresses", self._handle_stats_addresses)
        self.app.router.add_route("GET", "/stats/buffer", self._handle_stats_buffer)
        self.app.router.add_route("GET", "/stats/buffer/from/{from_id}", self._handle_stats_buffer_from)
        self.app.router.add_route("GET", "/stats/silo/{silo_name}", self._handle_stats_silo)
        self.app.router.add_route("GET", "/stats/silo/{silo_name}/agents", self._handle_stats_silo_agents)
        self.app.router.add_route("GET", "/stats/silo/{silo_name}/addresses", self._handle_stats_silo_addresses)
        self.app.router.add_route("GET", "/{path:.*}", self._handle_tarpit)
        self.app.router.add_route("HEAD", "/{path:.*}", self._handle_tarpit_head)

    # --- Stats endpoints ---

    async def _handle_stats(self, request: web.Request) -> web.Response:
        return web.json_response(self.stats.get_overview())

    async def _handle_stats_agents(self, request: web.Request) -> web.Response:
        return web.json_response(self.stats.get_agents())

    async def _handle_stats_addresses(self, request: web.Request) -> web.Response:
        return web.json_response(self.stats.get_addresses())

    async def _handle_stats_buffer(self, request: web.Request) -> web.Response:
        return web.json_response(self.stats.get_buffer())

    async def _handle_stats_buffer_from(self, request: web.Request) -> web.Response:
        from_id = request.match_info["from_id"]
        return web.json_response(self.stats.get_buffer(from_id=from_id))

    async def _handle_stats_silo(self, request: web.Request) -> web.Response:
        name = request.match_info["silo_name"]
        return web.json_response(self.stats.get_overview(silo=name))

    async def _handle_stats_silo_agents(self, request: web.Request) -> web.Response:
        name = request.match_info["silo_name"]
        return web.json_response(self.stats.get_agents(silo=name))

    async def _handle_stats_silo_addresses(self, request: web.Request) -> web.Response:
        name = request.match_info["silo_name"]
        return web.json_response(self.stats.get_addresses(silo=name))

    # --- Tarpit handler ---

    async def _handle_tarpit_head(self, request: web.Request) -> web.Response:
        silo = self._resolve_silo(request)
        if not silo:
            return web.Response(status=404)

        delay = random.uniform(silo.header_wait_min, silo.header_wait_max)
        await asyncio.sleep(delay)
        return web.Response(status=200, headers={"Content-Type": "text/html; charset=utf-8"})

    async def _handle_tarpit(self, request: web.Request) -> web.StreamResponse:
        cpu_start = time.process_time()
        wall_start = time.monotonic()
        path = "/" + request.match_info.get("path", "")
        client_ip = request.headers.get(self.config.real_ip_header, request.remote or "unknown")
        agent = request.headers.get("User-Agent", "unknown")

        silo = self._resolve_silo(request)
        if not silo:
            delay = random.uniform(
                self.config.min_wait * 0.1,
                self.config.max_wait * 0.1,
            )
            await asyncio.sleep(min(delay, 10))
            self.stats.record_hit(
                address=client_ip, agent=agent, uri=path,
                silo="bogon", response=404, bytes_generated=0,
                bytes_sent=0, delay=delay, cpu=time.process_time() - cpu_start,
                complete=True, bogon=True,
            )
            return web.Response(status=404, text="Not Found")

        silo_obj = self.silo_manager.get_silo(silo.name)

        if silo.bogon_filter and not silo_obj.validate_path(path):
            delay = random.uniform(silo.header_wait_min, silo.header_wait_max)
            await asyncio.sleep(delay)
            self.stats.record_hit(
                address=client_ip, agent=agent, uri=path,
                silo=silo.name, response=404, bytes_generated=0,
                bytes_sent=0, delay=delay, cpu=time.process_time() - cpu_start,
                complete=True, bogon=True,
            )
            return web.Response(status=404, text="Not Found")

        if silo.redirect_rate > 0 and random.randint(1, 100) <= silo.redirect_rate:
            delay = random.uniform(silo.header_wait_min, silo.header_wait_max)
            await asyncio.sleep(delay)
            redirect_url = silo_obj.generate_random_url()
            self.stats.record_hit(
                address=client_ip, agent=agent, uri=path,
                silo=silo.name, response=302, bytes_generated=0,
                bytes_sent=0, delay=delay, cpu=time.process_time() - cpu_start,
                complete=True, redirect=True,
            )
            return web.Response(status=302, headers={"Location": redirect_url})

        page_content = silo_obj.generate_page(path)
        page_bytes = page_content.encode("utf-8")
        bytes_generated = len(page_bytes)

        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Transfer-Encoding": "chunked",
            },
        )
        await response.prepare(request)

        bytes_sent = 0
        complete = True

        try:
            if silo.zero_delay:
                await response.write(page_bytes)
                bytes_sent = bytes_generated
            else:
                min_w = silo.min_wait if silo.min_wait is not None else self.config.min_wait
                max_w = silo.max_wait if silo.max_wait is not None else self.config.max_wait
                total_delay = random.uniform(min_w, max_w)

                chunk_count = max(10, bytes_generated // 50)
                delay_per_chunk = total_delay / chunk_count
                chunk_size = max(1, bytes_generated // chunk_count)

                offset = 0
                while offset < bytes_generated:
                    end = min(offset + chunk_size, bytes_generated)
                    await response.write(page_bytes[offset:end])
                    bytes_sent += (end - offset)
                    offset = end
                    if offset < bytes_generated:
                        await asyncio.sleep(delay_per_chunk)
        except (ConnectionResetError, ConnectionAbortedError, asyncio.CancelledError):
            complete = False

        wall_elapsed = time.monotonic() - wall_start
        cpu_elapsed = time.process_time() - cpu_start

        self.stats.record_hit(
            address=client_ip, agent=agent, uri=path,
            silo=silo.name, response=200, bytes_generated=bytes_generated,
            bytes_sent=bytes_sent, delay=wall_elapsed, cpu=cpu_elapsed,
            complete=complete,
        )

        try:
            await response.write_eof()
        except Exception:
            pass

        return response

    def _resolve_silo(self, request: web.Request) -> Optional[SiloConfig]:
        silo_header = request.headers.get(self.config.silo_header)
        path = "/" + request.match_info.get("path", "")

        if silo_header:
            cfg = self.config.get_silo_by_name(silo_header)
            if cfg:
                return cfg

        for silo_cfg in self.config.silos:
            for prefix in silo_cfg.prefixes:
                if path.startswith(prefix):
                    return silo_cfg

        return self.config.get_default_silo()

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()

        if self.config.unix_socket:
            site = web.UnixSite(runner, self.config.unix_socket)
        else:
            site = web.TCPSite(runner, self.config.http_host, self.config.http_port)

        await site.start()
        logger.info(
            "Nepenthes listening on %s",
            self.config.unix_socket or f"{self.config.http_host}:{self.config.http_port}",
        )

        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
        finally:
            await runner.cleanup()
