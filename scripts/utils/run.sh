#!/bin/bash
clear
echo "=========================================="
echo "  🚀 BI Solution - Iniciando Sistema"
echo "=========================================="

# Para e remove containers antigos
docker compose -f docker-compose.light.yml down 2>/dev/null

# Inicia containers
echo ""
echo "📦 Iniciando containers..."
docker compose -f docker-compose.light.yml up -d

# Aguarda backend ficar saudável
echo "⏳ Aguardando backend..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker compose -f docker-compose.light.yml ps | grep -q "agent_bi_backend.*healthy"; then
        break
    fi
    sleep 1
    timeout=$((timeout-1))
done

# Aguarda frontend
echo "⏳ Aguardando frontend..."
sleep 5

# Define URLs
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"

# Testa conectividade
echo ""
echo "🔍 Testando conectividade..."
if curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health | grep -q "200"; then
    echo "✅ Backend OK"
else
    echo "❌ Backend não respondeu"
fi

clear
echo "=========================================="
echo "  ✅ Sistema Iniciado com Sucesso!"
echo "=========================================="
echo ""
echo "🌐 Acesse agora:"
echo ""
echo "   👉 $FRONTEND_URL"
echo ""
echo "   Backend API: $BACKEND_URL"
echo "   Documentação: $BACKEND_URL/docs"
echo ""
echo "🔐 Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "=========================================="
echo ""

# Tenta abrir browser automaticamente no Windows
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "🌐 Abrindo navegador..."
    cmd.exe /c start $FRONTEND_URL 2>/dev/null || powershell.exe -c "Start-Process '$FRONTEND_URL'" 2>/dev/null
fi

echo "📝 Comandos úteis:"
echo "   Ver logs:  docker compose -f docker-compose.light.yml logs -f"
echo "   Parar:     docker compose -f docker-compose.light.yml down"
echo ""
