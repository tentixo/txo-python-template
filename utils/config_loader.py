# utils/config_loader.py
from typing import Tuple, Dict, Union, Any, Optional
from jsonschema import validate, ValidationError
import functools

from utils.logger import setup_logger
from utils.load_n_save import TxoDataHandler

logger = setup_logger()
data_handler = TxoDataHandler()


class ConfigLoader:
    def __init__(self, org_id: str, env_type: str, schema_filename: str = "org-env-config-schema.json") -> None:
        """
        Initialize the ConfigLoader with organization and environment details.

        Args:
            org_id (str): The organization identifier (e.g., "txo").
            env_type (str): The environment type (e.g., "test", "prod").
            schema_filename (str): The JSON schema filename (default: "org-env-config-schema.json").
        """
        self.org_id = org_id
        self.env_type = env_type
        self.schema_filename = schema_filename
        self._secrets: Optional[Dict[str, Any]] = None  # Cache for secrets
        self._config: Optional[Dict[str, Any]] = None  # Cache for config

    @property
    def config_filename(self) -> str:
        """Get the configuration filename for this org and environment."""
        return f"{self.org_id}-{self.env_type}-config.json"

    @property
    def secrets_filename(self) -> str:
        """Get the secrets filename for this org and environment."""
        return f"{self.org_id}-{self.env_type}-config-secrets.json"

    def validate_schema(self, config: Dict[str, Any]) -> None:
        """
        Validate the configuration against the JSON schema.

        Args:
            config (Dict[str, Any]): The configuration dictionary to validate.

        Raises:
            ValidationError: If the config does not match the schema.
            FileNotFoundError: If the schema file is missing.
        """
        try:
            schema = data_handler.load_json('schemas', self.schema_filename)
            validate(instance=config, schema=schema)
            logger.info(f"Config validated for org-env: {self.org_id}-{self.env_type}")
        except ValidationError as e:
            error_path = " > ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            logger.error(
                f"Invalid config for {self.org_id}-{self.env_type}: Error at '{error_path}' - {e.message}"
            )
            raise

    def load(self, _validate: bool = True) -> Dict[str, Any]:
        """
        Load the configuration JSON for the organization.

        Args:
            _validate (bool): Whether to validate the config against the schema (default: True).

        Returns:
            Dict[str, Any]: The configuration dictionary.

        Raises:
            FileNotFoundError: If the config file is missing.
            ValidationError: If validation fails and _validate is True.
        """
        # Return cached config if available
        if self._config is not None:
            return self._config

        try:
            self._config = data_handler.load_json('config', self.config_filename)
            if _validate:
                self.validate_schema(self._config)
            return self._config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_filename}")
            raise
        except ValidationError:
            # Don't log here since validate_schema already logs the error
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise

    def _load_secrets(self) -> Dict[str, Any]:
        """
        Load and cache the secrets JSON file.

        Returns:
            Dict[str, Any]: The secrets dictionary.

        Raises:
            FileNotFoundError: If the secrets file is missing.
        """
        if self._secrets is None:
            try:
                self._secrets = data_handler.load_json('config', self.secrets_filename)
            except FileNotFoundError:
                logger.error(f"Secrets file not found: {self.secrets_filename}")
                raise
            except Exception as e:
                logger.error(f"Error loading secrets: {e}")
                raise
        return self._secrets

    def get_token(self) -> str:
        """
        Load and return the raw Azure API token.

        Returns:
            str: The Bearer token string.

        Raises:
            KeyError: If "az-token" is missing in the secrets.
            FileNotFoundError: If the secrets file is missing.
        """
        secrets = self._load_secrets()
        token = secrets.get("az-token")
        if not token:
            logger.error("Azure token missing in secrets")
            raise KeyError("Missing Azure token in secrets")
        return token

    def get_headers(self) -> Dict[str, str]:
        """
        Load and return the Azure API headers for REST calls.

        Returns:
            Dict[str, str]: The headers dictionary with Authorization and Content-Type.

        Raises:
            KeyError: If "az-token" is missing in the secrets.
            FileNotFoundError: If the secrets file is missing.
        """
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_cb_user_password(self) -> str:
        """
        Load and return the Couchbase bucket password.

        Returns:
            str: The Couchbase bucket password.

        Raises:
            KeyError: If "cb-bucket-pwd" is not found in the secrets.
            FileNotFoundError: If the secrets file is missing.
        """
        secrets = self._load_secrets()
        cb_pwd = secrets.get("cb-user-pwd")
        if not cb_pwd:
            logger.error("Couchbase bucket password missing in secrets")
            raise KeyError("Missing Couchbase bucket password in secrets")
        return cb_pwd

    def get_oauth_tenant_id(self) -> str:
        """
        Get the OAuth tenant ID from the global config.

        Returns:
            str: The tenant ID

        Raises:
            KeyError: If "tenant-id" is not found in global config
            FileNotFoundError: If the config file is missing
        """
        config = self.load()
        tenant_id = config["global"].get("tenant-id")
        if not tenant_id:
            logger.error("Tenant ID missing in global config")
            raise KeyError("Missing tenant-id in global config")
        return tenant_id

    def get_oauth_client_id(self) -> str:
        """
        Get the OAuth client ID from the global config.

        Returns:
            str: The client ID

        Raises:
            KeyError: If "client-id" is not found in global config
            FileNotFoundError: If the config file is missing
        """
        config = self.load()
        client_id = config["global"].get("client-id")
        if not client_id:
            logger.error("Client ID missing in global config")
            raise KeyError("Missing client-id in global config")
        return client_id

    def get_oauth_client_secret(self) -> str:
        """
        Get the OAuth client secret from the secrets file.

        Returns:
            str: The client secret

        Raises:
            KeyError: If "client-secret" is not found in secrets
            FileNotFoundError: If the secrets file is missing
        """
        secrets = self._load_secrets()
        client_secret = secrets.get("client-secret")
        if not client_secret:
            logger.error("Client secret missing in secrets")
            raise KeyError("Missing client-secret in secrets")
        return client_secret

    def get_oauth_scope(self, default: str = "https://api.businesscentral.dynamics.com/.default") -> str:
        """
        Get the OAuth scope from the global config, with fallback to default.

        Args:
            default: Default scope if not specified in config

        Returns:
            str: The OAuth scope

        Raises:
            FileNotFoundError: If the config file is missing
        """
        config = self.load()
        return config["global"].get("oauth-scope", default)


@functools.lru_cache(maxsize=32)
def get_config_loader(org_id: str, env_type: str, schema_filename: str = "org-env-config-schema.json") -> ConfigLoader:
    """
    Get a cached ConfigLoader instance.

    Args:
        org_id (str): The organization identifier.
        env_type (str): The environment type.
        schema_filename (str): The schema filename.

    Returns:
        ConfigLoader: A cached instance of ConfigLoader.
    """
    return ConfigLoader(org_id, env_type, schema_filename)


def load_config_and_headers(
        org_id: str,
        env_type: str,
        return_config: bool = False,
        return_headers: bool = False,
        schema_filename: str = "org-env-config-schema.json"
) -> Union[Dict[str, Any], Tuple[Dict[str, Any], Dict[str, str]]]:
    """
    Load the configuration and/or headers for an organization.

    Args:
        org_id (str): The organization identifier (e.g., "txo").
        env_type (str): The environment type (e.g., "test", "prod").
        return_config (bool): If True, return the config dictionary (default: False).
        return_headers (bool): If True, return the headers dictionary (default: False).
        schema_filename (str): The JSON schema filename (default: "org-env-config-schema.json").

    Returns:
        Union[Dict[str, Any], Tuple[Dict[str, Any], Dict[str, str]]]: Config, headers, or both based on flags.

    Raises:
        ValueError: If neither config nor headers is requested.
    """
    if not (return_config or return_headers):
        raise ValueError("Specify what to return: set return_config and/or return_headers to True")

    loader = get_config_loader(org_id, env_type, schema_filename)
    result = []
    if return_config:
        result.append(loader.load())
    if return_headers:
        result.append(loader.get_headers())

    return tuple(result) if len(result) > 1 else result[0]
