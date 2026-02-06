#!/bin/bash
# Script para iniciar o BI Solution em Docker
# Uso: ./start.sh

set -e  # Para em caso de erro

echo "======================================"
echo "  BI Solution - Iniciando Docker"
echo "======================================"
echo ""

# Para containers existentes
echo "🛑 Parando containers existentes..."
docker compose -f docker-compose.light.yml down 2>/dev/null || true

echo ""
echo "🚀 Iniciando containers..."
docker compose -f docker-compose.light.yml up -d

echo ""
echo "⏳ Aguardando containers ficarem prontos..."
sleep 5

echo ""
echo "📊 Status dos containers:"
docker compose -f docker-compose.light.yml ps

echo ""
echo "======================================"
echo "  ✅ Sistema iniciado!"
echo "======================================"
echo ""
echo "🌐 Acessos:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "🔐 Credenciais:"
echo "  Username: admin"
echo "  Password: admin123 ou Admin@2024"
echo ""
echo "📝 Para ver logs em tempo real:"
echo "  docker compose -f docker-compose.light.yml logs -f"
echo ""
echo "🛑 Para parar:"
echo "  docker compose -f docker-compose.light.yml down"
echo "======================================"
