import secrets
import base64

def generate_secret_key():
    # Genera 32 byte di dati casuali
    random_bytes = secrets.token_bytes(32)
    # Codifica in base64 per avere una stringa leggibile
    secret_key = base64.b64encode(random_bytes).decode('utf-8')
    return secret_key

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"Chiave segreta generata: {secret_key}")
    print(f"Lunghezza: {len(secret_key)} caratteri") 