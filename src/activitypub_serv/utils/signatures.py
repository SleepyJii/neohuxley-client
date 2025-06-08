from fastapi import HTTPException, Request, APIRouter
import httpx
from typing import Optional, Dict
import json
import base64
from hashlib import sha256
from datetime import datetime
import re

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import serialization




async def fetch_public_key(key_url: str) -> Optional[str]:
    """Fetch the public key from a remote server using the keyId URL."""
    try:
        async with httpx.AsyncClient() as client:
            # Handle key IDs that are fragment identifiers
            if "#" in key_url:
                actor_url = key_id.split("#")[0]
            else:
                actor_url = key_url
                key_url += "#main-key"
            response = await client.get(
                actor_url,
                headers={"Accept": "application/activity+json"}
            )
            response.raise_for_status()
            actor_data = response.json()
            
            # Standard ActivityPub public key location
            if "publicKey" in actor_data and actor_data["publicKey"]["id"] == key_url:
                return actor_data["publicKey"]["publicKeyPem"]
            # Mastodon-compatible location
            elif "public_key" in actor_data:
                return f"""-----BEGIN PUBLIC KEY-----
{actor_data["public_key"]}
-----END PUBLIC KEY-----"""
            else:
                raise Exception("response did not contain public key")
                
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch public key: {str(e)}"
        )

async def verify_signature_header(request: Request) -> bool:
    signature_header = request.headers.get("Signature")

    # Parse Signature header into a dict
    def parse_signature(header: str) -> Dict[str, str]:
        pattern = r'(\w+)=["\']?([^,"\']+)["\']?'
        return dict(re.findall(pattern, header))

    parsed = parse_signature(signature_header)

    # Required components
    key_id = parsed.get("keyId")
    signature_b64 = parsed.get("signature")
    headers_list = parsed.get("headers", "").split()

    if not (key_id and signature_b64 and headers_list):
        raise Exception("Request missing some of (KeyId, signature, headers)")

    # Reconstruct signed string
    signed_lines = []
    for h in headers_list:
        h_lower = h.lower()
        if h_lower == "(request-target)":
            signed_lines.append(f"(request-target): {request.method.lower()} {request.url.scheme}:{request.url.path}")
        else:
            val = request.headers.get(h_lower)
            if val is None:
                raise Exception('header with None value')
            signed_lines.append(f"{h_lower}: {val}")
    signed_data = "\n".join(signed_lines)

    # Fetch sender's public key from keyId (assumes actor URI format)
    actor_uri = key_id.split("#")[0]
    public_key_pem = await fetch_public_key(actor_uri)
    public_key = serialization.load_pem_public_key(public_key_pem.encode())

    # this should raise Exception if invalid
    public_key.verify(
        base64.b64decode(signature_b64),
        signed_data.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )


def create_signature_header(request_target, headers, key_id, private_key_pem):
    # Build the string to sign
    headers_to_sign = [
        "(request-target): post " + request_target,
        f"host: {headers['Host']}",
        f"date: {headers['Date']}"
    ]
    signed_string = "\n".join(headers_to_sign)

    # Sign it
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None
    )
    signature = base64.b64encode(
        private_key.sign(
            signed_string.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    ).decode()

    # Construct the Signature header
    return (
        f'keyId="{key_id}",'
        f'algorithm="rsa-sha256",'
        f'headers="(request-target) host date",'
        f'signature="{signature}"'
    )

