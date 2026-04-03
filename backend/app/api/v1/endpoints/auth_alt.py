"""
ENDPOINT DE LOGIN ALTERNATIVO - USA PYODBC DIRETO (SÍNCRONO)
Bypass do problema com aioodbc

AVISO: Este endpoint usa conexão direta ao SQL Server local.
Deve permanecer DESABILITADO fora de ambiente controlado (USE_SQL_SERVER=false).
Credenciais de conexão são lidas exclusivamente via variáveis de ambiente:
  - PYODBC_CONNECTION_STRING  (string completa, preferencial)
  - ou combinar: DB_ALT_SERVER, DB_ALT_DATABASE, DB_ALT_USER, DB_ALT_PASSWORD
"""
import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import pyodbc
import bcrypt
from backend.app.config.security import create_access_token, create_refresh_token

router_alt = APIRouter(prefix="/auth-alt", tags=["Auth Alternative"])

class LoginRequest(BaseModel):
    username: str
    password: str

class UserData(BaseModel):
    id: str
    username: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserData

def _build_connection_string() -> str:
    """Constrói a connection string do SQL Server via variáveis de ambiente."""
    conn_str = os.environ.get("PYODBC_CONNECTION_STRING", "")
    if conn_str:
        return conn_str
    server   = os.environ.get("DB_ALT_SERVER", "")
    database = os.environ.get("DB_ALT_DATABASE", "agentbi")
    user     = os.environ.get("DB_ALT_USER", "")
    password = os.environ.get("DB_ALT_PASSWORD", "")
    if not server or not user or not password:
        raise ValueError(
            "Credenciais SQL Server não configuradas. "
            "Defina PYODBC_CONNECTION_STRING ou DB_ALT_SERVER/DB_ALT_USER/DB_ALT_PASSWORD no .env."
        )
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )

@router_alt.post("/login", response_model=Token)
def login_alt(login_data: LoginRequest):
    """
    Login alternativo usando pyodbc síncrono.
    Requer USE_SQL_SERVER=true e credenciais configuradas em variáveis de ambiente.
    """
    try:
        conn = pyodbc.connect(_build_connection_string(), timeout=5)
        cursor = conn.cursor()
        
        # Buscar usuário
        cursor.execute(
            "SELECT id, username, email, hashed_password, role, is_active FROM users WHERE username = ?",
            (login_data.username,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        user_id, username, email, hashed_password, role, is_active = user
        
        # Verificar senha
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verificar se está ativo
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Atualizar last_login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (str(user_id),)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Criar tokens
        token_data = {
            "sub": str(user_id),
            "username": username,
            "role": role,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Criar objeto de usuário
        user_data = UserData(
            id=str(user_id),
            username=username,
            email=email or "",
            role=role
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_data
        )
        
    except pyodbc.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
