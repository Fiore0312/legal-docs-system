import pytest
from fastapi import status
from datetime import datetime, timedelta
from ..app.core.security import create_access_token, verify_password
from ..app.models.user import User

def test_register_user(client):
    """
    Test registrazione nuovo utente.
    """
    response = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "Password123!",
        "full_name": "New User"
    })
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "password" not in data

def test_register_duplicate_email(client, test_user):
    """
    Test registrazione con email già esistente.
    """
    response = client.post("/auth/register", json={
        "email": test_user["email"],
        "password": "Password123!",
        "full_name": "Duplicate User"
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email già registrata" in response.json()["detail"]

def test_login_success(client, test_user):
    """
    Test login con credenziali valide.
    """
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": test_user["password"]
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client, test_user):
    """
    Test login con password errata.
    """
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": "wrong_password"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Credenziali non valide" in response.json()["detail"]

def test_login_invalid_email(client):
    """
    Test login con email non esistente.
    """
    response = client.post("/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "password123"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Credenziali non valide" in response.json()["detail"]

def test_get_current_user(client, test_user, auth_headers):
    """
    Test recupero utente corrente.
    """
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["full_name"] == test_user["full_name"]

def test_get_current_user_no_token(client):
    """
    Test accesso senza token.
    """
    response = client.get("/auth/me")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]

def test_get_current_user_invalid_token(client):
    """
    Test accesso con token non valido.
    """
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer invalid_token"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]

def test_update_user(client, test_user, auth_headers):
    """
    Test aggiornamento dati utente.
    """
    response = client.put("/auth/me", headers=auth_headers, json={
        "full_name": "Updated Name",
        "password": "NewPassword123!"
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"
    
    # Verifica nuovo login con password aggiornata
    response = client.post("/auth/login", data={
        "username": test_user["email"],
        "password": "NewPassword123!"
    })
    assert response.status_code == status.HTTP_200_OK

def test_delete_user(client, test_user, auth_headers, db):
    """
    Test eliminazione account.
    """
    response = client.delete("/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verifica che l'utente non esista più
    user = db.query(User).filter(User.email == test_user["email"]).first()
    assert user is None

def test_admin_get_users(client, test_user, test_admin, admin_headers):
    """
    Test recupero lista utenti (solo admin).
    """
    response = client.get("/auth/users", headers=admin_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # test_user + test_admin
    
    emails = [user["email"] for user in data]
    assert test_user["email"] in emails
    assert test_admin["email"] in emails

def test_user_get_users_forbidden(client, auth_headers):
    """
    Test accesso lista utenti negato a utenti normali.
    """
    response = client.get("/auth/users", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not enough permissions" in response.json()["detail"]

def test_admin_update_user(client, test_user, admin_headers):
    """
    Test modifica utente da parte dell'admin.
    """
    response = client.put(
        f"/auth/users/{test_user['id']}", 
        headers=admin_headers,
        json={
            "full_name": "Admin Updated",
            "is_active": False
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Admin Updated"
    assert not data["is_active"]

def test_admin_delete_user(client, test_user, admin_headers, db):
    """
    Test eliminazione utente da parte dell'admin.
    """
    response = client.delete(
        f"/auth/users/{test_user['id']}", 
        headers=admin_headers
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verifica che l'utente non esista più
    user = db.query(User).filter(User.email == test_user["email"]).first()
    assert user is None

def test_token_expiration():
    """
    Test scadenza token.
    """
    # Crea token scaduto
    expired_token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=timedelta(minutes=-10)
    )
    
    # Verifica che il token sia scaduto
    from jose import jwt, JWTError
    from ..app.core.config import get_settings
    
    settings = get_settings()
    
    with pytest.raises(JWTError):
        jwt.decode(
            expired_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        ) 