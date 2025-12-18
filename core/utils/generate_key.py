import secrets
import base64

key_b64 = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"SECRET_KEY={key_b64}")