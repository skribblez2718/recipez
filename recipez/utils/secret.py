import re
import json
import base64
import secrets
import time
import string
import hmac
import hashlib

from typing import List, Dict, Optional
from flask import (
    current_app,
    request,
)
from datetime import datetime, timezone
from argon2 import PasswordHasher
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from recipez.utils.error import RecipezErrorUtils


###################################[ start RecipezSecretsUtils ]###################################
class RecipezSecretsUtils:
    """
    Utility functions for secrets generation, hashing, JWT signing, and verification.
    """

    #########################[ start generate_secret ]#########################
    @staticmethod
    def generate_secret() -> str:
        """
        Securely generates a secret key.
        Returns:
            str: A randomly generated secret key.
        """
        return secrets.token_hex(64)

    #########################[ end generate_secret ]#########################

    #########################[ start validate_secret ]#########################
    @staticmethod
    def validate_secret(secret: str) -> bool:
        """
        Validates that a secret matches the expected format.
        Args:
            secret (str): The secret to validate.
        Returns:
            bool: True if the secret is valid, False otherwise.
        """
        pattern = r"^[a-f0-9]{60}$"
        return bool(re.match(pattern, secret))

    #########################[ end validate_secret ]#########################

    #########################[ start generate_hash ]#########################
    @staticmethod
    def generate_hash(to_hash: str) -> str:
        """
        Generate a hash using Argon2.
        Args:
            to_hash (str): The data to hash.
        Returns:
            str: The resulting hash.
        """
        ph = PasswordHasher(
            time_cost=current_app.config.get("RECIPEZ_ARGON_TIME_COST"),
            memory_cost=current_app.config.get("RECIPEZ_ARGON_MEMORY_COST"),
            parallelism=current_app.config.get("RECIPEZ_ARGON_PARALLELISM"),
            hash_len=current_app.config.get("RECIPEZ_ARGON_HASH_LEN"),
            salt_len=current_app.config.get("RECIPEZ_ARGON_SALT_LEN"),
        )
        return ph.hash(to_hash)

    #########################[ end generate_hash ]#########################

    #########################[ start compare_hash ]#########################
    @staticmethod
    def compare_hash(stored_hash: str, to_hash: str) -> bool:
        """
        Compare a hash with a generated hash.
        Args:
            stored_hash (str): The stored hash.
            to_hash (str): The data to hash.
        Returns:
            bool: True if the hashes match, False otherwise.
        """
        ph = PasswordHasher(
            time_cost=current_app.config.get("RECIPEZ_ARGON_TIME_COST"),
            memory_cost=current_app.config.get("RECIPEZ_ARGON_MEMORY_COST"),
            parallelism=current_app.config.get("RECIPEZ_ARGON_PARALLELISM"),
            hash_len=current_app.config.get("RECIPEZ_ARGON_HASH_LEN"),
            salt_len=current_app.config.get("RECIPEZ_ARGON_SALT_LEN"),
        )
        return ph.verify(stored_hash, to_hash)

    #########################[ end compare_hash ]#########################

    #########################[ start encrypt ]#########################
    @staticmethod
    def encrypt(to_encrypt: str) -> str:
        """
        Encrypts a string using AES-GCM.
        Args:
            to_encrypt (str): The string to encrypt.
        Returns:
            str: The encrypted string.
        """
        key_b64 = current_app.config.get("RECIPEZ_ENCRYPTION_KEY")
        key = base64.b64decode(key_b64)
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, to_encrypt.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    #########################[ end encrypt ]#########################

    #########################[ start decrypt ]#########################
    @staticmethod
    def decrypt(to_decrypt: str) -> str:
        """
        Decrypts a string using AES-GCM.
        Args:
            to_decrypt (str): The string to decrypt.
        Returns:
            str: The decrypted string.
        """
        encrypted_data = base64.b64decode(to_decrypt)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        key_b64 = current_app.config.get("RECIPEZ_ENCRYPTION_KEY")
        key = base64.b64decode(key_b64)
        aesgcm = AESGCM(key)
        plain_text = aesgcm.decrypt(nonce, ciphertext, None)
        return plain_text.decode("utf-8")

    #########################[ end decrypt ]#########################

    #########################[ start generate_hmac ]#########################
    @staticmethod
    def generate_hmac(to_hmac: str) -> str:
        """
        Generate a HMAC for a string.
        Args:
            to_hmac (str): The string to hash.
        Returns:
            str: The HMAC.
        """
        key = base64.b64decode(current_app.config.get("RECIPEZ_HMAC_SECRET"))
        to_hmac_normalized = to_hmac.strip().lower().encode()
        hmac_digest = hmac.new(key, to_hmac_normalized, hashlib.sha512).digest()
        return base64.b64encode(hmac_digest).decode("utf-8")

    #########################[ end generate_hmac ]#########################

    #########################[ start b64url_encode ]#########################
    @staticmethod
    def b64url_encode(data: bytes) -> str:
        """
        Encode bytes to a URL-safe Base64 string.
        Args:
            data (bytes): Data to encode.
        Returns:
            str: The Base64 encoded string.
        """
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    #########################[ end b64url_encode ]#########################

    #########################[ start generate_jwt ]#########################
    @staticmethod
    def generate_jwt(user_sub: str, scopes: List[str], additional_ai_scopes: List[str] = None) -> str:
        """
        Generate a JSON Web Token (JWT) for a user with specified scopes.
        Args:
            user_sub (str): The user's subject (username).
            scopes (List[str]): List of base scopes.
            additional_ai_scopes (List[str], optional): Additional AI-related scopes to include.
        Returns:
            str: The generated JWT.
        """
        # Merge base scopes with AI scopes
        merged_scopes = scopes.copy()
        if additional_ai_scopes:
            merged_scopes.extend(additional_ai_scopes)

        header = {"alg": "PS512", "typ": "JWT"}
        payload = {
            "sub": str(user_sub),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int(
                (
                    datetime.now(timezone.utc)
                    + current_app.config.get("RECIPEZ_JWT_EXPIRE_TIME")
                ).timestamp()
            ),
            "iss": current_app.config.get("RECIPEZ_JWT_ISSUER"),
            "aud": current_app.config.get("RECIPEZ_JWT_AUDIENCE"),
            "scope": merged_scopes,
        }
        encoded_header = RecipezSecretsUtils.b64url_encode(
            json.dumps(header, separators=(",", ":")).encode()
        )
        encoded_payload = RecipezSecretsUtils.b64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        signing_input = f"{encoded_header}.{encoded_payload}".encode()

        # Retrieve the RSA private key from the app config
        private_key = current_app.config.get("RECIPEZ_JWT_PRIVATE_KEY")
        signature = private_key.sign(
            signing_input,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512(),
        )
        encoded_signature = RecipezSecretsUtils.b64url_encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    #########################[ end generate_jwt ]#########################

    #########################[ start generate_api_key_jwt ]#########################
    @staticmethod
    def generate_api_key_jwt(
        user_sub: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None,
    ) -> str:
        """
        Generate a JWT for an API key with custom expiration.

        Args:
            user_sub (str): The user's subject (UUID).
            scopes (List[str]): List of scopes for the API key.
            expires_at (Optional[datetime]): Custom expiration datetime (None = 100 years).

        Returns:
            str: The generated JWT string.
        """
        from datetime import timedelta

        header = {"alg": "PS512", "typ": "JWT"}

        # Calculate expiration
        if expires_at is None:
            # "Never expires" = 100 years from now
            exp_timestamp = int(
                (datetime.now(timezone.utc) + timedelta(days=36500)).timestamp()
            )
        else:
            exp_timestamp = int(expires_at.timestamp())

        payload = {
            "sub": str(user_sub),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": exp_timestamp,
            "iss": current_app.config.get("RECIPEZ_JWT_ISSUER"),
            "aud": current_app.config.get("RECIPEZ_JWT_AUDIENCE"),
            "scope": scopes,
            "type": "api_key",  # Distinguish from session JWTs
        }

        encoded_header = RecipezSecretsUtils.b64url_encode(
            json.dumps(header, separators=(",", ":")).encode()
        )
        encoded_payload = RecipezSecretsUtils.b64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        signing_input = f"{encoded_header}.{encoded_payload}".encode()

        # Retrieve the RSA private key from the app config
        private_key = current_app.config.get("RECIPEZ_JWT_PRIVATE_KEY")
        signature = private_key.sign(
            signing_input,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512(),
        )
        encoded_signature = RecipezSecretsUtils.b64url_encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    #########################[ end generate_api_key_jwt ]#########################

    #########################[ start generate_jwt_hash ]#########################
    @staticmethod
    def generate_jwt_hash(jwt: str) -> str:
        """
        Generate an HMAC hash for a JWT (for revocation lookup).

        Unlike generate_hmac, this does NOT normalize the input since
        JWT strings are case-sensitive.

        Args:
            jwt (str): The full JWT string.

        Returns:
            str: Base64-encoded HMAC-SHA512 hash.
        """
        key = base64.b64decode(current_app.config.get("RECIPEZ_HMAC_SECRET"))
        # JWT is case-sensitive, do NOT normalize
        hmac_digest = hmac.new(key, jwt.encode(), hashlib.sha512).digest()
        return base64.b64encode(hmac_digest).decode("utf-8")

    #########################[ end generate_jwt_hash ]#########################

    #########################[ start b64url_decode ]#########################
    @staticmethod
    def b64url_decode(data: str) -> bytes:
        """
        Decode a URL-safe Base64 string to bytes.
        Args:
            data (str): Data to decode.
        Returns:
            bytes: The decoded bytes.
        """
        padding_str = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding_str)

    #########################[ end b64url_decode ]#########################

    #########################[ start verify_jwt ]#########################
    @staticmethod
    def verify_jwt(jwt: str) -> List[Optional[str]]:
        """
        Verify a JSON Web Token (JWT) using RSA-PSS verification.
        Args:
            jwt (str): The JWT string.
        Returns:
            List[str]: List of scopes if valid, empty list if invalid.
        """
        name = f"secrets.{RecipezSecretsUtils.verify_jwt.__name__}"
        response_msg = "JWT verification failed"

        try:
            # Input validation
            if not jwt or not isinstance(jwt, str):
                current_app.logger.warning(f"JWT verification failed: invalid input type or empty token")
                RecipezErrorUtils.handle_util_error(
                    name, request, "Invalid JWT input", response_msg
                )
                return []

            parts = jwt.split(".")
            if len(parts) != 3:
                current_app.logger.warning(f"JWT verification failed: invalid structure (parts: {len(parts)})")
                RecipezErrorUtils.handle_util_error(
                    name, request, "Invalid JWT structure", response_msg
                )
                return []

            header_b64, payload_b64, sig_b64 = parts

            # Verify signature
            try:
                signing_input = f"{header_b64}.{payload_b64}".encode()
                signature = RecipezSecretsUtils.b64url_decode(sig_b64)
            except Exception as e:
                current_app.logger.warning(f"JWT verification failed: signature decoding error - {str(e)}")
                RecipezErrorUtils.handle_util_error(
                    name, request, f"JWT signature decoding failed: {str(e)}", response_msg
                )
                return []

            if not RecipezSecretsUtils.verify_signature(signature, signing_input):
                current_app.logger.warning(f"JWT verification failed: signature verification failed")
                RecipezErrorUtils.handle_util_error(
                    name, request, "JWT signature verification failed", response_msg
                )
                return []

            # Parse payload
            try:
                payload_json = RecipezSecretsUtils.b64url_decode(payload_b64)
                payload = json.loads(payload_json)
            except json.JSONDecodeError as e:
                current_app.logger.warning(f"JWT verification failed: payload JSON decode error - {str(e)}")
                RecipezErrorUtils.handle_util_error(
                    name, request, f"JWT payload JSON decode failed: {str(e)}", response_msg
                )
                return []
            except Exception as e:
                current_app.logger.warning(f"JWT verification failed: payload decode error - {str(e)}")
                RecipezErrorUtils.handle_util_error(
                    name, request, f"JWT payload decode failed: {str(e)}", response_msg
                )
                return []

            # Verify claims
            if not RecipezSecretsUtils.verify_expiration(payload):
                # Expiration verification includes its own logging
                RecipezErrorUtils.handle_util_error(
                    name, request, "JWT token expired", response_msg
                )
                return []

            if not RecipezSecretsUtils.verify_issuer(payload):
                current_app.logger.warning(f"JWT verification failed: invalid issuer - {payload.get('iss')}")
                RecipezErrorUtils.handle_util_error(
                    name, request, "Invalid JWT issuer", response_msg
                )
                return []

            if not RecipezSecretsUtils.verify_audience(payload):
                current_app.logger.warning(f"JWT verification failed: invalid audience - {payload.get('aud')}")
                RecipezErrorUtils.handle_util_error(
                    name, request, "Invalid JWT audience", response_msg
                )
                return []

            return payload

        except Exception as e:
            current_app.logger.error(f"JWT verification unexpected error: {str(e)}")
            RecipezErrorUtils.handle_util_error(
                name, request, f"JWT verification unexpected error: {str(e)}", response_msg
            )
            return []

    #########################[ end verify_jwt ]#########################

    #########################[ start verify_signature ]#########################
    @staticmethod
    def verify_signature(signature: bytes, signing_input: bytes) -> bool:
        """
        Verify a signature using RSA-PSS verification.
        Args:
            signature (bytes): The signature to verify.
            signing_input (bytes): The input data to verify.
        Returns:
            bool: True if the signature is valid, False otherwise.
        """
        try:
            public_key = current_app.config.get("RECIPEZ_JWT_PUBLIC_KEY")
            public_key.verify(
                signature,
                signing_input,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA512()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA512(),
            )
            return True
        except Exception:
            return False

    #########################[ end verify_signature ]#########################

    #########################[ start verify_expiration ]#########################
    @staticmethod
    def verify_expiration(payload: Dict[str, str | int]) -> bool:
        """
        Verify the expiration time of a JWT.
        Args:
            payload (Dict[str, str | int]): The JWT payload.
        Returns:
            bool: True if the JWT is valid, False otherwise.
        """
        try:
            exp = payload.get("exp")
            if exp is None or not isinstance(exp, int):
                return False

            current_time = time.time()
            if current_time > exp:
                # Security: Add grace period check - reject tokens too far expired
                grace_period_seconds = 300  # 5 minutes grace period
                if current_time > (exp + grace_period_seconds):
                    current_app.logger.warning(
                        f"JWT token rejected: expired beyond grace period "
                        f"(expired: {exp}, current: {current_time}, grace: {grace_period_seconds}s)"
                    )
                    return False

                # Make sure the system JWT does not expire
                from recipez.repository import UserRepository

                system_user = UserRepository.get_user_by_id(
                    current_app.config.get("RECIPEZ_SYSTEM_USER_ID")
                )
                sub = payload.get("sub")
                if sub == system_user.user_sub:
                    if not RecipezSecretsUtils.verify_issuer(payload):
                        current_app.logger.warning(
                            f"System JWT renewal failed: invalid issuer for user {sub}"
                        )
                        return False

                    if not RecipezSecretsUtils.verify_audience(payload):
                        current_app.logger.warning(
                            f"System JWT renewal failed: invalid audience for user {sub}"
                        )
                        return False

                    # Log successful system JWT renewal for security audit
                    current_app.logger.info(
                        f"Renewing system JWT for user {sub} within grace period"
                    )
                    new_jwt = RecipezSecretsUtils.generate_jwt(
                        system_user.user_name,
                        current_app.config.get("RECIPEZ_SYSTEM_USER_JWT_SCOPES"),
                    )
                    current_app.config["RECIPEZ_SYSTEM_USER_JWT"] = new_jwt
                    return True

                # Non-system users cannot auto-renew tokens
                current_app.logger.warning(
                    f"JWT token expired for non-system user: {payload.get('sub')}"
                )
                return False
        except Exception as e:
            current_app.logger.error(
                f"JWT expiration verification failed: {str(e)}"
            )
            return False

        return True

    #########################[ end verify_expiration ]#########################

    #########################[ start verify_issuer ]#########################
    @staticmethod
    def verify_issuer(payload: Dict[str, str | int]) -> bool:
        """
        Verify the issuer of a JWT.
        Args:
            payload (Dict[str, str | int]): The JWT payload.
        Returns:
            bool: True if the JWT is valid, False otherwise.
        """
        try:
            expected_iss = current_app.config.get("RECIPEZ_JWT_EXPECTED_ISSUER")
            iss = payload.get("iss")
            if expected_iss and iss != expected_iss:
                return False
        except Exception:
            return False

        return True

    #########################[ end verify_issuer ]#########################

    #########################[ start verify_audience ]#########################
    @staticmethod
    def verify_audience(payload: Dict[str, str | int]) -> bool:
        """
        Verify the audience of a JWT.
        Args:
            payload (Dict[str, str | int]): The JWT payload.
        Returns:
            bool: True if the JWT is valid, False otherwise.
        """
        try:
            expected_aud = current_app.config.get("RECIPEZ_JWT_EXPECTED_AUDIENCE")
            aud = payload.get("aud")
            if expected_aud and aud != expected_aud:
                return False
        except Exception:
            return False

        return True

    #########################[ end verify_audience ]#########################

    #########################[ start gen_code_part ]#########################
    # Unambiguous character set - excludes visually similar characters:
    # Excluded: 0/O/o (zero vs oh), 1/l/I/i (one vs L vs i), 5/S/s, 8/B/b, 2/Z/z
    # Includes: digits 3,4,6,7,9 + uppercase A,C,D,E,F,G,H,J,K,M,N,P,Q,R,T,U,V,W,X,Y
    #           + lowercase a,c,d,e,f,g,h,j,k,m,n,p,q,r,t,u,v,w,x,y
    UNAMBIGUOUS_CHARS = "346789ACDEFGHJKMNPQRTUVWXYacdefghjkmnpqrtuvwxy"

    @staticmethod
    def gen_code_part() -> str:
        """
        Generate a random code part using unambiguous characters.

        Uses uppercase letters, lowercase letters, and digits that are
        visually distinct, excluding characters that can be confused
        with each other (0/O/o, 1/l/I/i, 5/S/s, 8/B/b, 2/Z/z).

        Returns:
            str: A random 4-character code part.
        """
        return "".join(
            secrets.choice(RecipezSecretsUtils.UNAMBIGUOUS_CHARS) for _ in range(4)
        )

    #########################[ end gen_code_part ]#########################

    #########################[ start is_jwt_expired_or_expiring ]#########################
    @staticmethod
    def is_jwt_expired_or_expiring(jwt: str, buffer_minutes: int = 10) -> bool:
        """
        Check if a JWT is expired or expiring within the specified buffer time.

        Args:
            jwt (str): The JWT token to check.
            buffer_minutes (int): Buffer time in minutes before expiration (default: 10).

        Returns:
            bool: True if JWT is expired or expiring, False otherwise.
        """
        try:
            # Input validation
            if not jwt or not isinstance(jwt, str):
                current_app.logger.warning("JWT expiration check failed: invalid input type or empty token")
                return True  # Treat invalid tokens as expired

            parts = jwt.split(".")
            if len(parts) != 3:
                current_app.logger.warning(f"JWT expiration check failed: invalid structure (parts: {len(parts)})")
                return True  # Treat malformed tokens as expired

            # Parse payload without full signature verification (for performance)
            try:
                payload_json = RecipezSecretsUtils.b64url_decode(parts[1])
                payload = json.loads(payload_json)
            except (json.JSONDecodeError, Exception) as e:
                current_app.logger.warning(f"JWT expiration check failed: payload decode error - {str(e)}")
                return True  # Treat unparseable tokens as expired

            # Check expiration with buffer
            exp = payload.get("exp")
            if exp is None or not isinstance(exp, int):
                current_app.logger.warning("JWT expiration check failed: missing or invalid exp claim")
                return True

            current_time = time.time()
            buffer_seconds = buffer_minutes * 60

            # Consider token expired if it expires within the buffer time
            is_expiring = current_time >= (exp - buffer_seconds)

            if is_expiring:
                current_app.logger.info(
                    f"JWT is expired or expiring within {buffer_minutes} minutes "
                    f"(exp: {exp}, current: {current_time}, buffer: {buffer_seconds}s)"
                )

            return is_expiring

        except Exception as e:
            current_app.logger.error(f"JWT expiration check unexpected error: {str(e)}")
            return True  # Treat any error as expired for safety

    #########################[ end is_jwt_expired_or_expiring ]#########################

    #########################[ start is_system_jwt ]#########################
    @staticmethod
    def is_system_jwt(jwt: str) -> bool:
        """
        Check if a JWT belongs to the system user.

        Args:
            jwt (str): The JWT token to check.

        Returns:
            bool: True if JWT belongs to system user, False otherwise.
        """
        try:
            # Input validation
            if not jwt or not isinstance(jwt, str):
                return False

            parts = jwt.split(".")
            if len(parts) != 3:
                return False

            # Parse payload without full signature verification
            try:
                payload_json = RecipezSecretsUtils.b64url_decode(parts[1])
                payload = json.loads(payload_json)
            except (json.JSONDecodeError, Exception):
                return False

            # Get system user information
            from recipez.repository import UserRepository

            system_user = UserRepository.get_system_user()
            if not system_user:
                current_app.logger.warning("System user not found when checking JWT")
                return False

            # Check if JWT subject matches system user
            jwt_sub = payload.get("sub")
            return jwt_sub == system_user.user_sub

        except Exception as e:
            current_app.logger.error(f"System JWT check failed: {str(e)}")
            return False

    #########################[ end is_system_jwt ]#########################

    #########################[ start renew_system_jwt ]#########################
    @staticmethod
    def renew_system_jwt() -> Optional[str]:
        """
        Renew the system user JWT and update the application configuration.

        Returns:
            Optional[str]: The new JWT if renewal was successful, None otherwise.
        """
        try:
            # Get system user
            from recipez.repository import UserRepository

            system_user = UserRepository.get_system_user()
            if not system_user:
                current_app.logger.error("System JWT renewal failed: system user not found")
                return None

            # Generate new JWT
            system_jwt_scopes = current_app.config.get("RECIPEZ_SYSTEM_USER_JWT_SCOPES", [])
            new_jwt = RecipezSecretsUtils.generate_jwt(
                system_user.user_sub,
                system_jwt_scopes
            )

            if not new_jwt:
                current_app.logger.error("System JWT renewal failed: JWT generation failed")
                return None

            # Update application configuration with thread safety
            current_app.config["RECIPEZ_SYSTEM_USER_JWT"] = new_jwt

            # Log successful renewal for security audit
            current_app.logger.info(
                f"System JWT successfully renewed for user: {system_user.user_name} "
                f"(sub: {system_user.user_sub})"
            )

            return new_jwt

        except Exception as e:
            current_app.logger.error(f"System JWT renewal failed: {str(e)}")
            return None

    #########################[ end renew_system_jwt ]#########################

    #########################[ start get_valid_system_jwt ]#########################
    @staticmethod
    def get_valid_system_jwt() -> Optional[str]:
        """
        Get a valid system JWT, renewing if expired or expiring.

        This method ensures a fresh JWT is always returned, handling
        multi-worker scenarios where cached JWTs may be stale.

        Returns:
            Optional[str]: Valid system JWT or None if renewal failed.
        """
        current_jwt = current_app.config.get("RECIPEZ_SYSTEM_USER_JWT")

        # If no JWT exists, attempt to generate one
        if not current_jwt:
            current_app.logger.warning("No system JWT found, attempting to generate")
            return RecipezSecretsUtils.renew_system_jwt()

        # Check if JWT needs renewal (expired or expiring within 10 minutes)
        if RecipezSecretsUtils.is_jwt_expired_or_expiring(current_jwt, buffer_minutes=10):
            new_jwt = RecipezSecretsUtils.renew_system_jwt()
            if new_jwt:
                return new_jwt
            # If renewal failed, try using current JWT as fallback
            current_app.logger.warning(
                "System JWT renewal failed, using existing JWT as fallback"
            )

        return current_jwt

    #########################[ end get_valid_system_jwt ]#########################


###################################[ end RecipezSecretsUtils ]###################################
