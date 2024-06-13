from datetime import datetime, timedelta
from typing import Literal, Tuple

import jwt

from anki_sync_server import APP_NAME


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
        try:
            decoded_token = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if (
                decoded_token.get("iss") == APP_NAME
                and decoded_token.get("type") == token_type
            ):
                return True, None
            else:
                return False, "Invalid issuer or token type"
        except jwt.ExpiredSignatureError:
            return False, "Token has expired"
        except jwt.InvalidTokenError:
            return False, "Invalid token"
