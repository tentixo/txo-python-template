# utils/config_loader.py
"""
Enhanced ConfigLoader with validation, caching, and thread safety.

Handles configuration and VAT levels with:
- JSON Schema validation
- Lazy imports for better startup time
- Thread-safe singleton pattern
- Memory-efficient caching
"""
import jsonschema
import sys
import threading
from typing import Dict, Any, Optional, Tuple
from weakref import WeakValueDictionary

from utils.logger import setup_logger
from utils.load_n_save import TxoDataHandler

logger = setup_logger()
data_handler = TxoDataHandler()

# Thread-safe cache for ConfigLoader instances
_loader_cache: WeakValueDictionary = WeakValueDictionary()
_cache_lock = threading.Lock()


class ConfigLoader:
    """
    Configuration loader with validation and caching.

    Features:
    - JSON Schema validation
    - Lazy loading and caching
    - Thread-safe operations
    - Memory-efficient design
    """

    # Memory optimization with __slots__
    __slots__ = ['org_id', 'env_type', '_config', '_vat_levels', '_lock']

    def __init__(self, org_id: str, env_type: str) -> None:
        """
        Initialize the ConfigLoader with organization and environment details.

        Args:
            org_id: The organization identifier (e.g., "txo")
            env_type: The environment type (e.g., "test", "prod")
        """
        self.org_id = org_id
        self.env_type = env_type
        self._config: Optional[Dict[str, Any]] = None  # Cache for config
        self._vat_levels: Optional[Dict[str, Any]] = None  # Cache for VAT levels
        self._lock = threading.Lock()  # Instance-level lock for thread safety

    @property
    def config_filename(self) -> str:
        """Get the configuration filename for this org and environment."""
        return f"{self.org_id}-{self.env_type}-config.json"

    @property
    def vat_levels_filename(self) -> str:
        """Get the VAT levels filename for this org and environment."""
        return f"{self.org_id}-{self.env_type}-vat-levels.json"

    def validate_schema(self, data: Dict[str, Any], schema_filename: str) -> None:
        """
        Validate data against the specified JSON schema.

        Uses lazy import of jsonschema for faster startup when validation
        is not needed.
        """
        # Now we know jsonschema is available, we can use it
        logger.debug(f"Starting schema validation: {schema_filename} for "
                     f"{self.org_id}-{self.env_type}")

        try:
            schema = data_handler.load_json('schemas', schema_filename)
        except FileNotFoundError as e:
            logger.error(f"❌ CRITICAL: Schema file not found: {schema_filename}")
            logger.error(f"Script cannot continue without schema validation: {e}")
            sys.exit(1)

        # Perform validation
        try:
            jsonschema.validate(instance=data, schema=schema)
            logger.info(f"✅ Schema validation successful: {schema_filename} for "
                        f"{self.org_id}-{self.env_type}")

        except jsonschema.ValidationError as e:
            # Handle validation errors
            error_path = " > ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            logger.error(
                f"❌ CRITICAL: Schema validation failed for {self.org_id}-{self.env_type}: "
                f"Error at '{error_path}' - {e.message}"
            )
            logger.error(f"Schema file: {schema_filename}")
            logger.error("Script cannot continue with invalid configuration.")
            sys.exit(1)

        except Exception as e:
            logger.error(f"❌ CRITICAL: Unexpected error during schema validation: {e}")
            sys.exit(1)

    def load_config(self, validate: bool = True, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load the main configuration JSON for the organization.

        Thread-safe loading with caching support.

        Args:
            validate: Whether to validate against schema (default: True)
            force_reload: Force reload even if cached (default: False)

        Returns:
            The configuration dictionary

        Raises:
            FileNotFoundError: If the config file is missing
            ValidationError: If validation fails and validate is True
        """
        with self._lock:
            # Return cached config if available and not forcing reload
            if self._config is not None and not force_reload:
                logger.debug(f"Returning cached config for {self.org_id}-{self.env_type}")
                return self._config

            try:
                self._config = data_handler.load_json('config', self.config_filename)

                if validate:
                    self.validate_schema(self._config, 'org-env-config-schema.json')

                logger.info(f"Loaded config: {self.config_filename}")
                return self._config

            except FileNotFoundError:
                logger.error(f"Config file not found: {self.config_filename}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error loading config: {e}")
                raise

    def load_vat_config(self, validate: bool = True, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load the VAT levels configuration JSON for the organization.

        Thread-safe loading with caching support.

        Args:
            validate: Whether to validate against schema (default: True)
            force_reload: Force reload even if cached (default: False)

        Returns:
            The VAT levels configuration dictionary

        Raises:
            FileNotFoundError: If the VAT levels file is missing
            ValidationError: If validation fails and validate is True
        """
        with self._lock:
            # Return cached VAT levels if available and not forcing reload
            if self._vat_levels is not None and not force_reload:
                logger.debug(f"Returning cached VAT levels for {self.org_id}-{self.env_type}")
                return self._vat_levels

            try:
                self._vat_levels = data_handler.load_json('config', self.vat_levels_filename)

                if validate:
                    self.validate_schema(self._vat_levels, 'org-env-vat-levels-schema.json')

                logger.info(f"Loaded VAT levels: {self.vat_levels_filename}")
                return self._vat_levels

            except FileNotFoundError:
                logger.error(f"VAT levels file not found: {self.vat_levels_filename}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error loading VAT levels: {e}")
                raise

    def load_all(self, validate: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Load both config and VAT levels in one call.

        Args:
            validate: Whether to validate against schemas

        Returns:
            Tuple of (config, vat_levels)
        """
        config = self.load_config(validate=validate)
        vat_levels = self.load_vat_config(validate=validate)
        return config, vat_levels

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a specific value from the configuration.

        Loads config if not already loaded.

        Args:
            key: Configuration key to retrieve
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load_config()

        return self._config.get(key, default)

    def get_vat_level(self, vat_code: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get a specific VAT level by code.

        Loads VAT config if not already loaded.

        Args:
            vat_code: VAT code to look up
            default: Default value if code not found

        Returns:
            VAT level percentage or default
        """
        if self._vat_levels is None:
            self.load_vat_config()

        vat_data = self._vat_levels.get('vat_levels', {}).get(vat_code, {})
        return vat_data.get('percentage', default)

    def clear_cache(self) -> None:
        """Clear cached configuration data."""
        with self._lock:
            self._config = None
            self._vat_levels = None
            logger.debug(f"Cleared cache for {self.org_id}-{self.env_type}")

    def reload(self, validate: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Force reload all configuration data.

        Args:
            validate: Whether to validate against schemas

        Returns:
            Tuple of (config, vat_levels)
        """
        self.clear_cache()
        return self.load_all(validate=validate)

    def __repr__(self) -> str:
        """String representation of ConfigLoader."""
        return f"ConfigLoader(org_id='{self.org_id}', env_type='{self.env_type}')"


def get_config_loader(org_id: str, env_type: str,
                      use_cache: bool = True) -> ConfigLoader:
    """
    Get or create a ConfigLoader instance.

    Uses caching to avoid creating multiple loaders for the same org/env.

    Args:
        org_id: Organization identifier
        env_type: Environment type
        use_cache: Whether to use cached instance if available

    Returns:
        ConfigLoader instance

    Example:
         loader = get_config_loader("txo", "prod")
         config = loader.load_config()
    """
    if not use_cache:
        return ConfigLoader(org_id, env_type)

    cache_key = f"{org_id}_{env_type}"

    with _cache_lock:
        if cache_key in _loader_cache:
            logger.debug(f"Returning cached ConfigLoader for {cache_key}")
            return _loader_cache[cache_key]

        loader = ConfigLoader(org_id, env_type)
        _loader_cache[cache_key] = loader
        logger.debug(f"Created and cached ConfigLoader for {cache_key}")
        return loader


class ConfigContext:
    """
    Context manager for configuration loading.

    Ensures configuration is loaded and optionally validated.

    Example:
         with ConfigContext("txo", "prod") as (config, vat_levels):
        ...     api_url = config['api_url']
        ...     vat_rate = vat_levels['vat_levels']['standard']['percentage']
    """

    def __init__(self, org_id: str, env_type: str,
                 validate: bool = True, use_cache: bool = True):
        """
        Initialize configuration context.

        Args:
            org_id: Organization identifier
            env_type: Environment type
            validate: Whether to validate configurations
            use_cache: Whether to use cached loader
        """
        self.org_id = org_id
        self.env_type = env_type
        self.validate = validate
        self.use_cache = use_cache
        self.loader: Optional[ConfigLoader] = None
        self.config: Optional[Dict[str, Any]] = None
        self.vat_levels: Optional[Dict[str, Any]] = None

    def __enter__(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Load configurations on context entry."""
        self.loader = get_config_loader(self.org_id, self.env_type, self.use_cache)
        self.config, self.vat_levels = self.loader.load_all(validate=self.validate)
        return self.config, self.vat_levels

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit."""
        # Could add cleanup logic here if needed
        pass