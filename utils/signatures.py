from fastapi import HTTPException, Request, APIRouter
from http_message_signatures import HTTPMessageSigner, HTTPMessageVerifier
from http_message_signatures import algorithms
from http_message_signatures.exceptions import InvalidSignature
import httpx
from typing import Optional
import json



async def fetch_public_key(key_id: str) -> Optional[str]:
    """Fetch the public key from a remote server using the keyId URL."""
    try:
        async with httpx.AsyncClient() as client:
            # Handle key IDs that are fragment identifiers
            if "#" in key_id:
                actor_url = key_id.split("#")[0]
                response = await client.get(
                    actor_url,
                    headers={"Accept": "application/activity+json"}
                )
                response.raise_for_status()
                actor_data = response.json()
                
                # Standard ActivityPub public key location
                if "publicKey" in actor_data and actor_data["publicKey"]["id"] == key_id:
                    return actor_data["publicKey"]["publicKeyPem"]
                
                # Mastodon-compatible location
                if "public_key" in actor_data:
                    return f"""-----BEGIN PUBLIC KEY-----
{actor_data["public_key"]}
-----END PUBLIC KEY-----"""
            
            # Direct key URL fallback
            response = await client.get(key_id)
            return response.text
                
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch public key: {str(e)}"
        )

async def verify_http_signature(request: Request) -> bool:
    """Verify the HTTP Signature using the http-message-signatures library."""
    try:
        # Create verifier with RSA-PSS algorithm
        verifier = HTTPMessageVerifier(
            signature_algorithm=algorithms.RSAPSSSignature(
                hash_algorithm=algorithms.HashAlgorithm.SHA256
            )
        )
        
        # Convert FastAPI request to verifiable format
        message = {
            "method": request.method,
            "target": request.url.path,
            "headers": [
                (name.lower(), value) 
                for name, value in request.headers.items()
                if name.lower() != "content-length"  # Exclude content-length as it may vary
            ],
        }
        
        # Add query params if present
        if request.url.query:
            message["target"] += f"?{request.url.query}"
        
        # Verify the signature
        verification = await verifier.verify(
            message=message,
            key_resolver=fetch_public_key
        )
        
        return verification is not None
        
    except InvalidSignature as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid signature: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Signature verification error: {str(e)}"
        )

