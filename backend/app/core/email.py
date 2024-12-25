from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any
import logging
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Configurazione email
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates'
)

# Inizializza FastMail
fastmail = FastMail(conf)

# Inizializza Jinja2 per i template
template_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent.parent / 'templates'))
)

async def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any]
) -> bool:
    """
    Invia una email usando un template HTML.
    """
    try:
        # Carica e renderizza il template
        template = template_env.get_template(f"{template_name}.html")
        html_content = template.render(**template_data)
        
        # Crea il messaggio
        message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            body=html_content,
            subtype="html"
        )
        
        # Invia l'email
        await fastmail.send_message(message)
        logger.info(f"Email inviata con successo a {email_to}")
        return True
        
    except ConnectionErrors as e:
        logger.error(f"Errore nell'invio dell'email a {email_to}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Errore generico nell'invio dell'email a {email_to}: {str(e)}")
        return False

async def send_verification_email(email_to: str, token: str) -> bool:
    """
    Invia l'email di verifica account.
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    template_data = {
        "verification_url": verification_url,
        "app_name": settings.APP_NAME,
        "support_email": settings.SUPPORT_EMAIL
    }
    
    return await send_email(
        email_to=email_to,
        subject="Verifica il tuo account",
        template_name="verification_email",
        template_data=template_data
    )

async def send_password_reset_email(email_to: str, token: str) -> bool:
    """
    Invia l'email per il reset della password.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    template_data = {
        "reset_url": reset_url,
        "app_name": settings.APP_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "valid_hours": 1  # Il token è valido per 1 ora
    }
    
    return await send_email(
        email_to=email_to,
        subject="Reset della password",
        template_name="reset_password_email",
        template_data=template_data
    )

async def send_password_change_notification(email_to: str) -> bool:
    """
    Invia una notifica di cambio password avvenuto.
    """
    template_data = {
        "app_name": settings.APP_NAME,
        "support_email": settings.SUPPORT_EMAIL
    }
    
    return await send_email(
        email_to=email_to,
        subject="Password modificata con successo",
        template_name="password_changed_email",
        template_data=template_data
    )

async def send_welcome_email(email_to: str, user_name: str) -> bool:
    """
    Invia l'email di benvenuto dopo la verifica dell'account.
    """
    template_data = {
        "user_name": user_name,
        "app_name": settings.APP_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "login_url": f"{settings.FRONTEND_URL}/login"
    }
    
    return await send_email(
        email_to=email_to,
        subject=f"Benvenuto in {settings.APP_NAME}!",
        template_name="welcome_email",
        template_data=template_data
    ) 