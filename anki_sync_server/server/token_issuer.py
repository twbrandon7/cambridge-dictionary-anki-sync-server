from datetime import datetime, timedelta
from typing import Literal, Tuple

import jwt

from anki_sync_server import APP_NAME
from anki_sync_server.setup.credential_storage import CredentialStorage


class TokenIssuer:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def issue(
        self, token_type: Literal["access", "refresh"], token_ttl: timedelta
    ) -> str:
        issue_datetime = datetime.now()
        expiration_datetime = issue_datetime + token_ttl
        payload = {
            "iss": APP_NAME,
            "iat": issue_datetime.timestamp(),
            "exp": expiration_datetime.timestamp(),
            "type": token_type,
        }
        if token_type == "refresh":
            CredentialStorage().set_refresh_token_created_at(payload["iat"])
            CredentialStorage().save()
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify(
        self, token: str, token_type: Literal["access", "refresh"]
    ) -> Tuple[bool, str | None]:
        """verify the given token

        Args:
            token (str): The token to verify
            token_type (Literal["access", "refresh"]): The expected token type
        Returns:
            Tuple[bool, str]: A tuple of a boolean indicating whether the token is
            valid and a error message
        """
        refresh_token_created_at = CredentialStorage().get_refresh_token_created_at()
        try:
            decoded_token = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if (
                token_type == "access"
                and decoded_token["type"] == token_type
                and decoded_token["iss"] == APP_NAME
            ):
                return True, None

            if (
                token_type == "refresh"
                and decoded_token["type"] == token_type
                and decoded_token["iss"] == APP_NAME
                and refresh_token_created_at is not None
                and refresh_token_created_at == decoded_token["iat"]
            ):
                return True, None

            return False, "Invalid token"
        except jwt.ExpiredSignatureError:
            return False, "Token has expired"
        except jwt.InvalidTokenError:
            return False, "Invalid token"
