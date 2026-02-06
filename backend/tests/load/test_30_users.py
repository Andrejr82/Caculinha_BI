"""
Teste de Carga - 30 Usuários Simultâneos

Usa Locust para simular 30 usuários acessando o sistema simultaneamente.
"""

from locust import HttpUser, task, between
import random


class BIUser(HttpUser):
    """Simula um usuário do sistema BI"""
    
    wait_time = between(1, 3)  # Espera 1-3 segundos entre requests
    
    def on_start(self):
        """Executado quando usuário inicia"""
        # Login (se necessário)
        self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
    
    @task(3)
    def query_vendas(self):
        """Query de vendas (mais frequente)"""
        queries = [
            "Quanto vendeu a loja 1685?",
            "Quais os produtos mais vendidos?",
            "Qual a margem média?",
            "Mostre as vendas do último mês"
        ]
        
        self.client.post("/api/v1/chat", json={
            "query": random.choice(queries),
            "session_id": f"session_{self.environment.runner.user_count}"
        })
    
    @task(2)
    def calcular_eoq(self):
        """Cálculo de EOQ"""
        self.client.post("/api/v1/tools/calcular_eoq", json={
            "produto_id": random.choice(["59294", "369946", "12345"])
        })
    
    @task(1)
    def prever_demanda(self):
        """Previsão de demanda"""
        self.client.post("/api/v1/tools/prever_demanda_sazonal", json={
            "produto_id": "59294",
            "periodo_dias": random.choice([30, 60, 90])
        })
    
    @task(1)
    def dashboard_metrics(self):
        """Métricas de dashboard"""
        self.client.get("/api/v1/metrics/executive-kpis")


# Executar teste:
# locust -f test_30_users.py --host=http://localhost:8000 --users=30 --spawn-rate=5
