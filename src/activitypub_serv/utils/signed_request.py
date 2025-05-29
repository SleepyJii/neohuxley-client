from http_message_signatures import (
    Signer,
    Algorithm,
    Header,
    SignatureParameters,
    HttpField,
    Component
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import datetime
import httpx

# Load private key
#with open("identities/alice/private.pem", "rb") as f:
#    private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())


def send_signed_request(body, destination_host, private_key, actor_key_id):


    # Build the signer
    signer = Signer(
        key=private_key,
        algorithm=Algorithm.RSA_SHA256,
    )

    # Define headers to sign
    fields = [
        Component("@method"),
        Component("@path"),
        Component("host"),
        Component("date"),
        Component("digest"),
    ]

    # Compose the request
    headers = {
        "Host": destination_host,
        "Date": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "Content-Type": "application/activity+json",
    }
    #body = b'{"type": "Follow", "actor": "https://your.server/actors/alice", "object": "https://remote.example/actors/bob"}'
    headers["Digest"] = "SHA-256=" + httpx._content.digest_body(body, "sha-256")

    # Signature parameters
    sig_params = SignatureParameters(
        key_id=actor_key_id, #'https://your.server/actors/alice#main-key',
        created=int(datetime.datetime.utcnow().timestamp()),
    )

    # Sign the request
    signature = signer.sign(
        fields=[HttpField(f) for f in fields],
        parameters=sig_params,
        covered_component_values=headers,
    )

    # Add signature header
    headers["Signature"] = signature

    # Example sending
    response = httpx.post(f"https://{destination_host}/inbox", headers=headers, content=body)



