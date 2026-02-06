"""
ENDPOINT DE LOGIN ALTERNATIVO - USA PYODBC DIRETO (SÍNCRONO)
Bypass do problema com aioodbc
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import pyodbc
import bcrypt
from app.config.security import create_access_token, create_refresh_token

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

@router_alt.post("/login", response_model=Token)
def login_alt(login_data: LoginRequest):
    """
    Login alternativo usando pyodbc síncrono
    """
    try:
        # Conectar diretamente com pyodbc
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=FAMILIA\\SQLJR,1433;"
            "DATABASE=agentbi;"
            "UID=AgenteVirtual;"
            "PWD=Cacula@2020;"
            "TrustServerCertificate=yes;",
            timeout=5
        )
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
