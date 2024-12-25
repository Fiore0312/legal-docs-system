from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any
import logging

from ...core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_email_verification_token,
    create_password_reset_token
)
# Commento temporaneamente le funzionalità email
# from ...core.email import (
#     send_verification_email,
#     send_password_reset_email,
#     send_password_change_notification,
#     send_welcome_email
# )
from ...core.config import get_settings
from ...db.database import get_db
from ...models.user import User, UserStatus
from ...schemas.user import UserCreate, UserResponse, Token, UserLogin
from ..deps import get_current_user

# Configurazione del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Registra un nuovo utente.
    """
    logger.debug(f"Tentativo di registrazione per email: {user_in.email}")
    try:
        # Verifica connessione database
        logger.debug("Verificando connessione al database...")
        if not db:
            logger.error("Connessione al database non disponibile")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database non disponibile"
            )

        # Verifica se l'email esiste già
        logger.debug("Verificando utente esistente...")
        user = db.query(User).filter(User.email == user_in.email).first()
        logger.debug(f"Risultato verifica utente esistente: {user is not None}")
        
        if user:
            logger.warning(f"Tentativo di registrazione con email già esistente: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email già registrata nel sistema"
            )
        
        # Hashing password
        logger.debug("Generazione hash password...")
        hashed_password = get_password_hash(user_in.password)
        logger.debug("Hash password generato con successo")
        
        # Creazione token di attivazione
        logger.debug("Generazione token di attivazione...")
        activation_token = create_email_verification_token(user_in.email)
        logger.debug("Token di attivazione generato con successo")
        
        # Creazione nuovo utente
        logger.debug("Creazione nuovo utente nel database...")
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            status=UserStatus.ACTIVE,  # Impostiamo lo stato come ACTIVE
            activation_token=activation_token,
            email_verified=True,  # Impostiamo email come già verificata
            is_active=True  # Impostiamo l'utente come attivo
        )
        
        db.add(user)
        logger.debug("Commit delle modifiche al database...")
        db.commit()
        db.refresh(user)
        logger.info(f"Utente creato con successo: ID={user.id}")
        
        # Commento temporaneamente l'invio email
        # background_tasks.add_task(
        #     send_verification_email,
        #     email_to=user.email,
        #     token=activation_token
        # )
        # logger.info("Task email di verifica aggiunto con successo")
        
        return user
        
    except HTTPException as he:
        # Rilancia le HTTPException senza modifiche
        logger.error(f"HTTPException durante la registrazione: {str(he)}")
        raise
        
    except Exception as e:
        logger.error(f"Errore durante la registrazione: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la registrazione: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Incrementa il contatore di tentativi falliti
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()
            if user.failed_login_attempts >= 5:
                user.status = UserStatus.SUSPENDED
            db.commit()
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account non attivo"
        )
    
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account sospeso per troppi tentativi di accesso falliti"
        )
    
    # Reset contatore tentativi falliti
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token.
    """
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token di refresh non valido"
            )
            
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato o non attivo"
            )
            
        access_token = create_access_token(user.id, user.role.value)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token di refresh non valido"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifica l'email dell'utente.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token non valido"
            )
            
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
            
        if user.email_verified:
            return {"message": "Email già verificata"}
            
        user.email_verified = True
        user.is_active = True
        user.status = UserStatus.ACTIVE
        user.activation_token = None
        db.commit()
        
        # Invia email di benvenuto in background
        background_tasks.add_task(
            send_welcome_email,
            email_to=user.email,
            user_name=user.first_name or user.email
        )
        
        return {"message": "Email verificata con successo"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token non valido o scaduto"
        )

@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Richiedi il reset della password.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Verifica il rate limiting per il reset password
        now = datetime.utcnow()
        if user.reset_token_expires and user.reset_token_expires > now:
            attempts = getattr(user, "password_reset_attempts", 0)
            if attempts >= settings.PASSWORD_RESET_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Troppi tentativi di reset password. Riprova più tardi."
                )
            
        # Genera nuovo token e aggiorna il contatore
        token = create_password_reset_token(email)
        user.reset_password_token = token
        user.reset_token_expires = now + timedelta(hours=1)
        user.password_reset_attempts = getattr(user, "password_reset_attempts", 0) + 1
        db.commit()
        
        # Invia email di reset in background
        background_tasks.add_task(
            send_password_reset_email,
            email_to=email,
            token=token
        )
    
    return {
        "message": "Se l'email esiste nel sistema, riceverai le istruzioni per il reset della password"
    }

@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset della password con token.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token non valido"
            )
            
        email = payload.get("sub")
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not user.reset_password_token or user.reset_password_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token non valido o scaduto"
            )
            
        if user.reset_token_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token scaduto"
            )
            
        # Aggiorna la password
        user.hashed_password = get_password_hash(new_password)
        user.reset_password_token = None
        user.reset_token_expires = None
        user.password_reset_attempts = 0
        user.password_changed_at = datetime.utcnow()
        db.commit()
        
        # Invia notifica cambio password in background
        background_tasks.add_task(
            send_password_change_notification,
            email_to=user.email
        )
        
        return {"message": "Password aggiornata con successo"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token non valido o scaduto"
        ) 