import logging
from typing import Optional
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from mcp.server.auth.provider import (
    AccessToken,
    OAuthAuthorizationServerProvider
)

# Set up logger
logger = logging.getLogger(__name__)

class KeycloakAccessToken(AccessToken):
    pass

class KeycloakOAuthProvider(OAuthAuthorizationServerProvider):
    def __init__(
        self,
        server_url: str,
        realm_name: str,
        client_id: Optional[str] = None
    ):
        self.server_url = server_url
        self.realm_name = realm_name
        self.client_id = client_id
        
        logger.info(f"Initializing Keycloak provider for realm: {realm_name}")
        logger.debug(f"Server URL: {server_url}")
        logger.debug(f"Client ID: {client_id}")
        
        try:
            self.keycloak_openid = KeycloakOpenID(
                server_url=server_url,
                realm_name=realm_name,
                client_id=client_id
            )
            logger.info("Successfully connected to Keycloak server")
        except Exception as e:
            logger.error(f"Failed to initialize Keycloak connection: {str(e)}")
            raise

    async def load_access_token(self, token: str) -> Optional[KeycloakAccessToken]:
        """Validate access token with debug logging"""        
        try:
            token_info = self.keycloak_openid.decode_token(
                token,
            )
            logger.debug("Access token validation successful")
            return KeycloakAccessToken(
                token=token,
                client_id=token_info.get("azp", ""),
                # Doing something very wrong here
                scopes=token_info['realm_access']['roles'],
                expires_at=token_info.get("exp")
            )
        except KeycloakError as e:
            logger.error(f"Keycloak token validation error: {e.response_body}")
            return None
        except Exception as e:
            logger.error(f"Access token validation failed: {str(e)}")
            return None