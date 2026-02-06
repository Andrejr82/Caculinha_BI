@echo off
echo ====================================================================
echo   DIAGNOSTICO SQL SERVER - Agent BI
echo ====================================================================
echo.

echo [1/6] Verificando servico SQL Server...
sc query MSSQLSERVER | findstr "ESTADO"
if %errorlevel% neq 0 (
    echo ERRO: Servico MSSQLSERVER nao encontrado
) else (
    echo OK: Servico encontrado
)
echo.

echo [2/6] Verificando se porta 1433 esta em uso...
netstat -an | findstr ":1433" > nul
if %errorlevel% neq 0 (
    echo PROBLEMA: Porta 1433 NAO esta em uso
    echo         O TCP/IP provavelmente NAO esta habilitado
) else (
    echo OK: Porta 1433 esta em uso
)
echo.

echo [3/6] Listando drivers ODBC instalados...
powershell -Command "Get-OdbcDriver | Where-Object {$_.Name -like '*SQL Server*'} | Select-Object -ExpandProperty Name | Select-Object -First 5"
echo.

echo [4/6] Verificando arquivo Parquet...
if exist "data\parquet\admmat.parquet" (
    echo OK: Arquivo admmat.parquet encontrado em data\parquet\
    for %%A in ("data\parquet\admmat.parquet") do echo    Tamanho: %%~zA bytes
) else if exist "backend\data\parquet\admmat.parquet" (
    echo OK: Arquivo admmat.parquet encontrado em backend\data\parquet\
    for %%A in ("backend\data\parquet\admmat.parquet") do echo    Tamanho: %%~zA bytes
) else (
    echo PROBLEMA: Arquivo Parquet NAO encontrado
)
echo.

echo [5/6] Testando conexao SQL Server...
sqlcmd -S localhost -U AgenteVirtual -P "Cacula@2020" -Q "SELECT @@VERSION" -h -1 2>nul
if %errorlevel% neq 0 (
    echo PROBLEMA: Nao foi possivel conectar ao SQL Server
    echo          Verifique HABILITAR_TCP_IP_SQL_SERVER.md
) else (
    echo OK: Conexao estabelecida com sucesso
)
echo.

echo [6/6] Verificando banco Projeto_Caculinha...
sqlcmd -S localhost -U AgenteVirtual -P "Cacula@2020" -d Projeto_Caculinha -Q "SELECT COUNT(*) FROM admmatao" -h -1 2>nul
if %errorlevel% neq 0 (
    echo PROBLEMA: Nao foi possivel acessar tabela admmatao
) else (
    echo OK: Tabela admmatao acessivel
)
echo.

echo ====================================================================
echo   RESUMO
echo ====================================================================
echo.
echo Se houver problemas acima, siga o guia:
echo   HABILITAR_TCP_IP_SQL_SERVER.md
echo.
echo Apos resolver, execute:
echo   cd backend\scripts
echo   python sync_sql_to_parquet.py
echo.
pause
