# utils/script_runner.py
"""
Enhanced script runner utilities with improved error handling and flexibility.

Provides robust script initialization with:
- OAuth token acquisition with caching
- Flexible argument parsing
- Configuration validation with secrets injection
- Context manager support
- Enhanced error recovery
- Clear, actionable error messages
"""

import argparse
import sys
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

import requests

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.oauth_helpers import OAuthClient
from utils.exceptions import ApiAuthenticationError, HelpfulError

# Initial logger without context
logger = setup_logger()


@dataclass
class ArgumentDefinition:
    """
    Definition for a command-line argument.

    Attributes:
        name: Argument name
        type: Argument type (str, int, float, bool)
        help: Help text for the argument
        default: Default value (makes argument optional)
        choices: List of valid choices
        required: Whether argument is required
        action: Argparse action (e.g., 'store_true')
    """
    name: str
    type: type = str
    help: str = ""
    default: Any = None
    choices: Optional[List[Any]] = None
    required: bool = True
    action: Optional[str] = None


class ScriptRunner:
    """
    Enhanced script runner with configuration management and token handling.
    """

    def __init__(self, description: str,
                 require_token: bool = True,
                 validate_config: bool = True,
                 cache_token: bool = True):
        """
        Initialize script runner.

        Args:
            description: Script description for help text
            require_token: Whether to acquire OAuth token
            validate_config: Whether to validate config against schema
            cache_token: Whether to use token caching
        """
        self.description = description
        self.require_token = require_token
        self.validate_config = validate_config
        self.cache_token = cache_token
        self.config: Optional[Dict[str, Any]] = None
        self.oauth_client: Optional[OAuthClient] = None
        self.logger = logger  # Store initial logger reference

    def get_access_token(self, config: Dict[str, Any],
                         retry_count: int = 3,
                         retry_delay: float = 2.0) -> str:
        """
        Get access token with enhanced error handling and retry logic.

        Uses OAuth configuration from config and injected secrets.

        Args:
            config: Loaded configuration dictionary with injected secrets
            retry_count: Number of retry attempts
            retry_delay: Delay between retries (doubled each retry)

        Returns:
            Access token string

        Raises:
            HelpfulError: If all token acquisition methods fail
        """
        org_id = config["_org_id"]
        env_type = config["_env_type"]

        # Try OAuth client credentials with retry
        oauth_errors = []
        for attempt in range(retry_count):
            try:
                # Extract OAuth configuration from main config
                tenant_id = config.get("global", {}).get("tenant-id")
                client_id = config.get("global", {}).get("client-id")
                oauth_scope = config.get("global", {}).get("oauth-scope")

                # Get client secret from injected secrets
                client_secret = config.get("_client_secret")  # Injected from secrets

                if not all([tenant_id, client_id, oauth_scope, client_secret]):
                    missing = []
                    if not tenant_id:
                        missing.append("tenant-id (in config)")
                    if not client_id:
                        missing.append("client-id (in config)")
                    if not oauth_scope:
                        missing.append("oauth-scope (in config)")
                    if not client_secret:
                        missing.append("client-secret (in secrets)")

                    raise HelpfulError(
                        what_went_wrong=f"OAuth configuration incomplete. Missing: {', '.join(missing)}",
                        how_to_fix="Add the missing OAuth configuration to your config and secrets files",
                        example="""Config file should have:
{
  "global": {
    "tenant-id": "your-tenant-id",
    "client-id": "your-client-id",
    "oauth-scope": "https://api.businesscentral.dynamics.com/.default"
  }
}

Secrets file should have:
{
  "client-secret": "your-client-secret"
}"""
                    )

                self.logger.info(f"OAuth token acquisition attempt {attempt + 1}/{retry_count}...")

                # Use cached OAuth client if available
                if not self.oauth_client:
                    self.oauth_client = OAuthClient(
                        tenant_id=tenant_id,
                        cache_tokens=self.cache_token
                    )

                token = self.oauth_client.get_client_credentials_token(
                    client_id=client_id,
                    client_secret=client_secret,
                    scope=oauth_scope,
                    tenant_id=tenant_id
                )

                self.logger.info("✅ Successfully acquired token via OAuth client credentials")
                return token

            except (requests.HTTPError, ApiAuthenticationError) as e:
                oauth_errors.append(str(e))
                if attempt < retry_count - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.warning(f"OAuth attempt {attempt + 1} failed: {e}")
                    self.logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(f"All OAuth attempts failed. Errors: {oauth_errors}")

            except Exception as e:
                self.logger.warning(f"Unexpected error during OAuth: {e}")
                oauth_errors.append(str(e))
                break

        # Fallback to pre-generated token from secrets (injected as _az_token)
        self.logger.info("Attempting fallback to injected token from secrets...")

        try:
            token = config.get("_az_token")  # Injected from secrets
            if not token:
                raise KeyError("No fallback token available")

            self.logger.info("✅ Successfully using fallback token from secrets")

            # Validate token format (basic check)
            if len(token) < 20:
                raise ValueError("Invalid token format")

            return token

        except KeyError:
            secrets_filename = f"{org_id}-{env_type}-config-secrets.json"
            raise HelpfulError(
                what_went_wrong="Failed to acquire authentication token",
                how_to_fix="Either fix the OAuth configuration or add a fallback token to secrets",
                example=f"""OAuth errors: {', '.join(oauth_errors)}

To add a fallback token, update config/{secrets_filename}:
{{
  "az-token": "your-token-here"
}}"""
            )
        except ValueError as e:
            raise HelpfulError(
                what_went_wrong=f"Invalid fallback token in secrets: {e}",
                how_to_fix="Update the 'az-token' in your secrets file with a valid token",
                example="Tokens should be long alphanumeric strings"
            )

    def parse_arguments(self, extra_args: Optional[List[ArgumentDefinition]] = None) -> argparse.Namespace:
        """
        Parse command-line arguments with validation.

        Args:
            extra_args: Optional list of additional argument definitions

        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Standard arguments - always required
        parser.add_argument("org_id", help="Organization ID (e.g., 'txo')")
        parser.add_argument("env_type", help="Environment type (e.g., 'test', 'prod')")

        # Common optional arguments
        parser.add_argument(
            "--no-token",
            action="store_true",
            help="Skip token acquisition (for non-API scripts)"
        )
        parser.add_argument(
            "--no-validation",
            action="store_true",
            help="Skip configuration validation"
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging"
        )

        # Add extra arguments if provided
        if extra_args:
            for arg_def in extra_args:
                kwargs: Dict[str, Any] = {
                    "help": arg_def.help,
                }

                # Handle optional vs required arguments
                if arg_def.default is not None or not arg_def.required:
                    arg_name = f"--{arg_def.name.replace('_', '-')}"
                    kwargs["default"] = arg_def.default
                    kwargs["required"] = arg_def.required
                else:
                    arg_name = arg_def.name

                # Add type if not using action
                if not arg_def.action:
                    kwargs["type"] = arg_def.type
                else:
                    kwargs["action"] = arg_def.action

                # Add choices if specified
                if arg_def.choices:
                    kwargs["choices"] = list(arg_def.choices)

                parser.add_argument(arg_name, **kwargs)

        args = parser.parse_args()

        # Set debug logging if requested
        if args.debug:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            self.logger.debug("Debug logging enabled")

        return args

    def load_configuration(self, args: argparse.Namespace,
                           extra_args: Optional[List[ArgumentDefinition]] = None) -> Dict[str, Any]:
        """
        Load and validate configuration with token acquisition.

        Args:
            args: Parsed command-line arguments
            extra_args: Optional list of argument definitions for injection

        Returns:
            Complete configuration dictionary with injected values

        Raises:
            HelpfulError: If configuration loading fails
        """
        # Set logger context as early as possible
        global logger
        logger = setup_logger(org_id=args.org_id)
        self.logger = logger
        self.logger.info(f"Starting {self.description} for {args.org_id}-{args.env_type}")

        try:
            # Load the main configuration with secrets
            config_loader = ConfigLoader(args.org_id, args.env_type)

            # Use validation flag (can be overridden by command line)
            should_validate = self.validate_config and not getattr(args, 'no_validation', False)

            # Load config with secrets automatically injected
            config = config_loader.load_config(
                validate=should_validate,
                include_secrets=True  # Secrets are injected with underscore prefix
            )

        except HelpfulError:
            # Re-raise HelpfulError as-is
            raise
        except Exception as e:
            # Convert other errors to HelpfulError
            raise HelpfulError(
                what_went_wrong=f"Failed to load configuration: {e}",
                how_to_fix="Check that your config file exists and is valid JSON",
                example=f"Expected file: config/{args.org_id}-{args.env_type}-config.json"
            )

        # Inject standard fields
        config["_org_id"] = args.org_id
        config["_env_type"] = args.env_type

        # Inject extra arguments if provided
        if extra_args:
            for arg_def in extra_args:
                attr_name = arg_def.name.replace('-', '_')
                if hasattr(args, attr_name):
                    config[f"_{attr_name}"] = getattr(args, attr_name)

        # Get token if required (can be overridden by command line)
        if self.require_token and not getattr(args, 'no_token', False):
            try:
                token = self.get_access_token(config)
                config["_token"] = token
            except HelpfulError:
                raise
            except Exception as e:
                raise HelpfulError(
                    what_went_wrong=f"Token acquisition failed: {e}",
                    how_to_fix="Check your OAuth configuration or add a fallback token",
                    example="See previous error messages for specific issues"
                )
        else:
            self.logger.info("Token acquisition skipped")
            config["_token"] = None

        self.config = config
        return config

    def run(self, extra_args: Optional[List[ArgumentDefinition]] = None) -> Dict[str, Any]:
        """
        Main entry point to parse arguments and load configuration.

        Args:
            extra_args: Optional list of additional argument definitions

        Returns:
            Complete configuration dictionary

        Raises:
            HelpfulError: If any step fails
        """
        args = self.parse_arguments(extra_args)
        return self.load_configuration(args, extra_args)


def parse_custom_args_and_load_config(
        description: str,
        custom_args: Optional[List[Tuple[str, type, str]]] = None,
        require_token: bool = True,
        validate_config: bool = True,
        cache_token: bool = True) -> Dict[str, Any]:
    """
    Parse command line arguments (including custom ones) and load configuration.

    Enhanced version that accepts additional custom arguments beyond org_id and env_type.

    Args:
        description: Script description for help text
        custom_args: Optional list of extra arguments as tuples of (name, type, help_text)
        require_token: Whether to acquire OAuth token
        validate_config: Whether to validate configuration
        cache_token: Whether to use token caching

    Returns:
        Dict containing loaded config with injected arguments and token

    Raises:
        SystemExit: On error, after printing helpful message

    Example:
         config = parse_custom_args_and_load_config(
        ...     "Batch processor",
        ...     custom_args=[
        ...         ("batch_size", int, "Number of items per batch"),
        ...         ("dry_run", bool, "Run without making changes")
        ...     ]
        ... )
    """
    # Convert old-style tuple arguments to ArgumentDefinition
    arg_definitions = None
    if custom_args:
        arg_definitions = [
            ArgumentDefinition(name=name, type=arg_type, help=help_text)
            for name, arg_type, help_text in custom_args
        ]

    try:
        # Use the enhanced ScriptRunner
        runner = ScriptRunner(
            description=description,
            require_token=require_token,
            validate_config=validate_config,
            cache_token=cache_token
        )

        return runner.run(extra_args=arg_definitions)

    except HelpfulError as e:
        # Log the helpful error message and exit
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        # Unexpected error - still provide some help
        logger.error(f"Unexpected error: {e}")
        logger.info("Try running with --debug flag for more details")
        import traceback
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        sys.exit(1)


def parse_args_and_load_config(description: str,
                               require_token: bool = True,
                               validate_config: bool = True) -> Dict[str, Any]:
    """
    Parse command line arguments and load configuration with OAuth token acquisition.

    Standard function for scripts that only need org_id and env_type.

    Args:
        description: Script description for help text
        require_token: Whether to acquire OAuth token (default: True)
        validate_config: Whether to validate configuration (default: True)

    Returns:
        Dict containing loaded config with injected org_id, env_type, and token

    Raises:
        SystemExit: On error, after printing helpful message

    Example:
         config = parse_args_and_load_config("My data processor")
         print(config['_org_id'])  # From command line
         print(config['_token'])   # OAuth token
         print(config['_client_secret'])  # From secrets file
    """
    return parse_custom_args_and_load_config(
        description=description,
        custom_args=None,  # No custom args, just org_id and env_type
        require_token=require_token,
        validate_config=validate_config,
        cache_token=True
    )


@contextmanager
def script_context(description: str,
                   extra_args: Optional[List[ArgumentDefinition]] = None,
                   require_token: bool = True,
                   setup_func: Optional[Callable[[Dict[str, Any]], None]] = None,
                   teardown_func: Optional[Callable[[Dict[str, Any]], None]] = None):
    """
    Context manager for script execution with automatic setup/teardown.

    Args:
        description: Script description
        extra_args: Optional additional arguments
        require_token: Whether to acquire token
        setup_func: Optional setup function to call with config
        teardown_func: Optional teardown function to call with config

    Yields:
        Configuration dictionary

    Example:
         with script_context("My Script") as config:
        ...     # Script logic here
        ...     api = create_rest_api(config)
        ...     api.get(url)
    """
    config = None
    start_time = time.time()

    try:
        # Initialize and run script runner
        runner = ScriptRunner(
            description=description,
            require_token=require_token
        )
        config = runner.run(extra_args=extra_args)

        # Run setup function if provided
        if setup_func:
            setup_func(config)

        logger.info(f"Script initialization complete for {config['_org_id']}-{config['_env_type']}")

        yield config

    except HelpfulError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise

    finally:
        # Run teardown function if provided
        if teardown_func and config:
            try:
                teardown_func(config)
            except Exception as e:
                logger.error(f"Teardown failed: {e}")

        # Log execution time
        elapsed = time.time() - start_time
        logger.info(f"Script execution completed in {elapsed:.2f}s")


def create_argument(*args, **kwargs) -> ArgumentDefinition:
    """
    Helper function to create an ArgumentDefinition.

    Shorthand for creating argument definitions.

    Example:
         arg = create_argument("batch_size", int, "Batch size", default=100)
    """
    return ArgumentDefinition(*args, **kwargs)