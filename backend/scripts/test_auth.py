import os
import sys
from pathlib import Path
import requests
import json
from datetime import datetime

# Aggiungi la directory root del progetto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# URL base dell'API
BASE_URL = "http://localhost:8000"

def test_registration():
    print("\n🔍 Test Registrazione Utente")
    print("-" * 50)
    
    # Dati per la registrazione
    user_data = {
        "email": "test@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        print("Risposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        # Test email duplicata
        print("\n🔍 Test Email Duplicata")
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        print("Risposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print("❌ Errore durante la registrazione:", str(e))

def test_login():
    print("\n🔍 Test Login")
    print("-" * 50)
    
    # Dati per il login
    login_data = {
        "username": "test@example.com",  # FastAPI OAuth2 usa 'username' invece di 'email'
        "password": "Password123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)  # Usa data invece di json per form data
        print(f"Status Code: {response.status_code}")
        print("Risposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data
            
    except Exception as e:
        print("❌ Errore durante il login:", str(e))
        return None

def test_me(token_data):
    print("\n🔍 Test Endpoint /me")
    print("-" * 50)
    
    if not token_data:
        print("❌ Token non disponibile, impossibile testare /me")
        return
        
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Risposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print("❌ Errore durante il test /me:", str(e))

def test_refresh_token(token_data):
    print("\n🔍 Test Refresh Token")
    print("-" * 50)
    
    if not token_data or 'refresh_token' not in token_data:
        print("❌ Refresh token non disponibile")
        return
        
    try:
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": token_data['refresh_token']}
        )
        print(f"Status Code: {response.status_code}")
        print("Risposta:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print("❌ Errore durante il refresh del token:", str(e))

def main():
    print("\n🚀 Inizio Test Sistema di Autenticazione")
    print("=" * 50)
    
    # Test registrazione
    test_registration()
    
    # Test login e ottieni token
    token_data = test_login()
    
    # Test endpoint /me
    test_me(token_data)
    
    # Test refresh token
    test_refresh_token(token_data)
    
    print("\n✅ Test Completati")

if __name__ == "__main__":
    main() 