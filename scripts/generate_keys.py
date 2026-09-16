#!/usr/bin/env python3
"""Print .env values for SECRET_KEY / EDGE_FERNET_KEY / EDGE_HMAC_SECRET."""
from __future__ import annotations

import secrets


def main():
    try:
        from cryptography.fernet import Fernet

        fernet = Fernet.generate_key().decode()
    except Exception:
        fernet = "(pip install cryptography) then re-run"
    print("# Paste into .env")
    print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
    print(f"EDGE_FERNET_KEY={fernet}")
    print(f"EDGE_HMAC_SECRET={secrets.token_urlsafe(32)}")
    print("ADMIN_USERNAME=admin")
    print("ADMIN_PASSWORD=Admin@123")
    print("DATABASE_URL=postgresql+asyncpg://ibvap:ibvap@localhost:5432/ibvap")
    print("ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173")
    print("FUSION_STATE_PATH=./fusion_state.json")
    print("ENVIRONMENT=development")


if __name__ == "__main__":
    main()
