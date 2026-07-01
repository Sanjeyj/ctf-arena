"""
DockerService
=============
Wraps Docker CLI interaction via subprocess (shell=False).

Two operating modes
-------------------
  REAL   — Docker daemon is reachable; containers are created/stopped/removed
           using the `docker` CLI binary.
  SIMULATED — Docker daemon is unreachable or `docker` binary is absent.
           All operations are faked in-process so the rest of the platform
           continues to work normally.  Simulated containers are stored in
           ``_sim_store`` (a plain Python dict keyed by fake container ID).

The mode is detected once at startup (``_probe_docker``) and can be queried
with ``DockerService.mode()``.

Public API
----------
  DockerService.mode()             → 'real' | 'simulated'
  DockerService.pull_image(ref)    → (ok, message)
  DockerService.run_container(...) → (ok, container_id, host_port, message)
  DockerService.stop_container(id) → (ok, message)
  DockerService.remove_container(id) → (ok, message)
  DockerService.container_status(id) → dict | None
  DockerService.get_logs(id, tail) → str
"""

from __future__ import annotations

import json
import logging
import random
import subprocess
import uuid
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simulation storage (in-process; per worker, non-persistent — acceptable for
# a fallback / dev mode).
# ---------------------------------------------------------------------------
_sim_store: dict[str, dict] = {}


def _probe_docker() -> bool:
    """Return True if the Docker daemon is reachable via the CLI."""
    try:
        result = subprocess.run(
            ['docker', 'info', '--format', '{{.ServerVersion}}'],
            capture_output=True,
            timeout=5,
            shell=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return False


_DOCKER_AVAILABLE: bool = _probe_docker()
if _DOCKER_AVAILABLE:
    logger.info('[DockerService] Real Docker mode active.')
else:
    logger.warning('[DockerService] Docker daemon unreachable — running in SIMULATION mode.')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Run a Docker CLI command safely (shell=False, no string concatenation).
    Raises RuntimeError on non-zero exit.
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def _find_free_port(start: int = 10000, end: int = 20000) -> int:
    """Return a random port in [start, end] — good enough for dev/CTF use."""
    return random.randint(start, end)


# ---------------------------------------------------------------------------
# DockerService
# ---------------------------------------------------------------------------

class DockerService:

    @staticmethod
    def mode() -> str:
        return 'real' if _DOCKER_AVAILABLE else 'simulated'

    # ------------------------------------------------------------------
    # Image operations
    # ------------------------------------------------------------------

    @staticmethod
    def pull_image(ref: str) -> Tuple[bool, str]:
        """Pull a Docker image by reference (e.g. 'ubuntu:22.04')."""
        if not _DOCKER_AVAILABLE:
            msg = f'[SIM] Pull {ref}: success (simulated).'
            logger.debug(msg)
            return True, msg
        try:
            _run(['docker', 'pull', ref], timeout=120)
            return True, f'Image {ref} pulled successfully.'
        except RuntimeError as exc:
            return False, str(exc)

    @staticmethod
    def image_exists(ref: str) -> bool:
        """Return True if the image is locally available."""
        if not _DOCKER_AVAILABLE:
            return True  # sim: always "available"
        try:
            _run(['docker', 'image', 'inspect', ref])
            return True
        except RuntimeError:
            return False

    # ------------------------------------------------------------------
    # Container lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    def run_container(
        image_ref: str,
        *,
        container_name: Optional[str] = None,
        host_port: Optional[int] = None,
        container_port: Optional[int] = None,
        env: Optional[dict] = None,
        cpu_limit: float = 0.5,
        memory_limit: str = '128m',
        pids_limit: int = 64,
        network_disabled: bool = False,
        extra_args: Optional[list] = None,
    ) -> Tuple[bool, str, Optional[int], str]:
        """
        Start a container.

        Returns (ok, container_id, host_port, message).
        host_port is the mapped port on the Docker host (None if no port mapping).
        """
        if not _DOCKER_AVAILABLE:
            return DockerService._sim_run(
                image_ref,
                container_name=container_name,
                host_port=host_port,
                container_port=container_port,
                env=env,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                pids_limit=pids_limit,
            )

        # Real Docker path ---------------------------------------------------
        if host_port is None and container_port is not None:
            host_port = _find_free_port()

        cmd = ['docker', 'run', '-d']

        if container_name:
            cmd += ['--name', container_name]

        cmd += ['--cpus', str(cpu_limit)]
        cmd += ['--memory', memory_limit]
        cmd += ['--pids-limit', str(pids_limit)]

        if network_disabled:
            cmd += ['--network', 'none']

        if host_port and container_port:
            cmd += ['-p', f'{host_port}:{container_port}']

        if env:
            for k, v in env.items():
                cmd += ['-e', f'{k}={v}']

        if extra_args:
            cmd += extra_args

        cmd.append(image_ref)

        try:
            result = _run(cmd)
            container_id = result.stdout.strip()[:64]
            logger.info('[DockerService] Started container %s (image=%s port=%s)', container_id, image_ref, host_port)
            return True, container_id, host_port, 'Container started.'
        except RuntimeError as exc:
            return False, '', None, str(exc)

    @staticmethod
    def stop_container(container_id: str) -> Tuple[bool, str]:
        if not _DOCKER_AVAILABLE:
            return DockerService._sim_stop(container_id)
        try:
            _run(['docker', 'stop', container_id])
            return True, f'Container {container_id[:12]} stopped.'
        except RuntimeError as exc:
            return False, str(exc)

    @staticmethod
    def remove_container(container_id: str) -> Tuple[bool, str]:
        if not _DOCKER_AVAILABLE:
            return DockerService._sim_remove(container_id)
        try:
            _run(['docker', 'rm', '-f', container_id])
            return True, f'Container {container_id[:12]} removed.'
        except RuntimeError as exc:
            return False, str(exc)

    @staticmethod
    def container_status(container_id: str) -> Optional[dict]:
        """Return a dict with 'status', 'running', 'image', or None if not found."""
        if not _DOCKER_AVAILABLE:
            return DockerService._sim_status(container_id)
        try:
            fmt = '{"id":"{{.Id}}","status":"{{.State.Status}}","running":{{.State.Running}},"image":"{{.Config.Image}}"}'
            result = _run(['docker', 'inspect', '--format', fmt, container_id])
            return json.loads(result.stdout.strip())
        except (RuntimeError, json.JSONDecodeError):
            return None

    @staticmethod
    def get_logs(container_id: str, tail: int = 100) -> str:
        if not _DOCKER_AVAILABLE:
            return f'[SIM] No real logs for simulated container {container_id[:12]}.'
        try:
            result = _run(['docker', 'logs', '--tail', str(tail), container_id])
            return result.stdout + result.stderr
        except RuntimeError as exc:
            return str(exc)

    # ------------------------------------------------------------------
    # Simulation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sim_run(
        image_ref: str,
        *,
        container_name=None,
        host_port=None,
        container_port=None,
        env=None,
        cpu_limit=0.5,
        memory_limit='128m',
        pids_limit=64,
    ) -> Tuple[bool, str, Optional[int], str]:
        if host_port is None and container_port is not None:
            host_port = _find_free_port()
        fake_id = uuid.uuid4().hex
        _sim_store[fake_id] = {
            'id': fake_id,
            'status': 'running',
            'running': True,
            'image': image_ref,
            'name': container_name,
            'host_port': host_port,
        }
        logger.info('[SIM] run container %s image=%s port=%s', fake_id[:12], image_ref, host_port)
        return True, fake_id, host_port, '[SIM] Container started (simulated).'

    @staticmethod
    def _sim_stop(container_id: str) -> Tuple[bool, str]:
        entry = _sim_store.get(container_id)
        if not entry:
            return False, f'[SIM] Container {container_id[:12]} not found.'
        entry['status'] = 'exited'
        entry['running'] = False
        return True, f'[SIM] Container {container_id[:12]} stopped.'

    @staticmethod
    def _sim_remove(container_id: str) -> Tuple[bool, str]:
        entry = _sim_store.pop(container_id, None)
        if not entry:
            return False, f'[SIM] Container {container_id[:12]} not found.'
        return True, f'[SIM] Container {container_id[:12]} removed.'

    @staticmethod
    def _sim_status(container_id: str) -> Optional[dict]:
        return _sim_store.get(container_id)
