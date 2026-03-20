"""
Teste de carga homologatorio para a stack ativa do ChatBI.

Mede:
- latencia do endpoint de capabilities
- emissao de stream token
- stream SSE do chat ate o evento final

Uso:
  set RUN_LOAD_TESTS=1
  locust -f backend/tests/load/test_chat_stream_homologation.py --host=http://localhost:8000 --users=30 --spawn-rate=5
"""

import json
import os
import random
import time
from datetime import datetime, timedelta

import jwt
import pytest

pytestmark = [pytest.mark.load, pytest.mark.external]

if os.getenv("RUN_LOAD_TESTS", "0") != "1":
    pytest.skip(
        "teste de carga manual; defina RUN_LOAD_TESTS=1 para executar com Locust.",
        allow_module_level=True,
    )

pytest.importorskip("locust", reason="Locust não instalado para teste de carga.")
from locust import HttpUser, between, task

from backend.app.api.middleware.auth import JWT_ALGORITHM, JWT_SECRET


def _env_ms(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = default
    return max(100, value)


CAPABILITIES_MAX_MS = _env_ms("CHAT_LOAD_CAPABILITIES_MAX_MS", 1000)
STREAM_TOKEN_MAX_MS = _env_ms("CHAT_LOAD_STREAM_TOKEN_MAX_MS", 1000)
STREAM_FINAL_MAX_MS = _env_ms("CHAT_LOAD_STREAM_FINAL_MAX_MS", 5000)


class ChatStreamUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        username = f"load.user.{random.randint(1000, 9999)}@agentbi.com"
        self.headers = {"Authorization": f"Bearer {self._issue_token(username)}"}

    def _issue_token(self, username: str) -> str:
        payload = {
            "sub": username,
            "user_id": username,
            "username": username,
            "email": username,
            "role": "admin",
            "tenant_id": "default",
            "exp": datetime.utcnow() + timedelta(minutes=10),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @task(2)
    def chat_capabilities(self):
        with self.client.get(
            "/api/v1/chat/capabilities",
            headers=self.headers,
            name="/api/v1/chat/capabilities",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"status inesperado: {response.status_code}")
                return
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)
            if elapsed_ms > CAPABILITIES_MAX_MS:
                response.failure(f"latencia {elapsed_ms}ms acima do SLO {CAPABILITIES_MAX_MS}ms")
                return
            response.success()

    @task(1)
    def chat_stream_token(self):
        with self.client.post(
            "/api/v1/chat/stream-token",
            headers=self.headers,
            name="/api/v1/chat/stream-token",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"status inesperado: {response.status_code}")
                return
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)
            if elapsed_ms > STREAM_TOKEN_MAX_MS:
                response.failure(f"latencia {elapsed_ms}ms acima do SLO {STREAM_TOKEN_MAX_MS}ms")
                return
            response.success()

    @task(3)
    def chat_stream_until_final(self):
        query = random.choice(
            [
                "oi",
                "quais são os kpis",
                "bom dia",
            ]
        )
        session_id = f"load-{random.randint(1000, 9999)}"
        started_at = time.perf_counter()
        saw_final = False

        with self.client.get(
            "/api/v1/chat/stream",
            params={"q": query, "session_id": session_id},
            headers=self.headers,
            name="/api/v1/chat/stream",
            catch_response=True,
            stream=True,
            timeout=max(10, int(STREAM_FINAL_MAX_MS / 1000) + 5),
        ) as response:
            if response.status_code != 200:
                response.failure(f"status inesperado: {response.status_code}")
                return

            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                payload = raw_line.replace("data: ", "", 1)
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "final":
                    saw_final = True
                    break

            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            if not saw_final:
                response.failure("stream nao concluiu com evento final")
                return
            if elapsed_ms > STREAM_FINAL_MAX_MS:
                response.failure(f"latencia final {elapsed_ms}ms acima do SLO {STREAM_FINAL_MAX_MS}ms")
                return
            response.success()
