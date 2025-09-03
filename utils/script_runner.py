# utils/script_runner.py
"""
Enhanced script runner utilities with v2.1 best practices.

Provides robust script initialization with:
- OAuth token acquisition with caching
- Configuration validation (always on)
- Hard-fail philosophy
- Clear, actionable error messages
"""

import argparse
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.oauth_helpers import OAuthClient
from utils.exceptions import HelpfulError

# Module logger - don't modify globally
logger = setup_logger()


@dataclass
class ArgumentDefinition:
    """Definition for a command-line argument."""
    name: str
    type: type = str
    help: str = ""
    default: Any = None
    choices: Optional[List[Any]] = None
    required: bool = True
    action: Optional[str] = None


class ScriptRunner:
    """Enhanced script runner with configuration management."""

    def __init__(self, description: str, require_token: bool = True):
        """
        Initialize script runner.

        Args:
            description: Script description for help text
            require_token: Whether to acquire OAuth token
        """
        self.description = description
        self.require_token = require_token
        self.oauth_client: Optional[OAuthClient] = None

    def parse_arguments(self, extra_args: Optional[List[ArgumentDefinition]] = None) -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Required arguments - always needed
        parser.add_argument("org_id", help="Organization ID (e.g., 'txo')")
        parser.add_argument("env_type", help="Environment type (e.g., 'test', 'prod')")

        # Add extra arguments if provided
        if extra_args:
            for arg_def in extra_args:
                kwargs: Dict[str, Any] = {"help": arg_def.help}

                # Handle optional vs required
                if arg_def.default is not None or not arg_def.required:
                    arg_name = f"--{arg_def.name.replace('_', '-')}"
                    kwargs["default"] = arg_def.default
                    kwargs["required"] = arg_def.required
                else:
                    arg_name = arg_def.name

                if not arg_def.action:
                    kwargs["type"] = arg_def.type
                else:
                    kwargs["action"] = arg_def.action

                if arg_def.choices:
                    kwargs["choices"] = arg_def.choices

                parser.add_argument(arg_name, **kwargs)

        return parser.parse_args()

    def load_configuration(self, org_id: str, env_type: str) -> Dict[str, Any]:
        """
        Load and validate configuration.

        ALWAYS validates against schema - no escape hatch!

        Args:
            org_id: Organization identifier
            env_type: Environment type

        Returns:
            Configuration dictionary with injected fields

        Raises:
            HelpfulError: If configuration loading fails
        """
        # Create logger with context
        ctx_logger = setup_logger(org_id=org_id)
        ctx_logger.info(f"Starting {self.description} for {org_id}-{env_type}")

        try:
            # Load configuration - ALWAYS validate
            config_loader = ConfigLoader(org_id, env_type)
            config = config_loader.load_config(
                validate=True,  # Always validate - no escape!
                include_secrets=True
            )

        except HelpfulError:
            raise  # Already formatted nicely
        except FileNotFoundError:
            raise HelpfulError(
                what_went_wrong=f"Configuration file not found for {org_id}-{env_type}",
                how_to_fix=f"Create config/{org_id}-{env_type}-config.json",
                example="Copy config/example.json as a template"
            )
        except Exception as e:
            raise HelpfulError(
                what_went_wrong=f"Configuration error: {e}",
                how_to_fix="Check your config file is valid JSON and matches the schema",
                example=f"Validate against schemas/org-env-config-schema.json"
            )

        # Inject standard fields (hard-coded, always present)
        config["_org_id"] = org_id
        config["_env_type"] = env_type

        return config

    def acquire_token(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Acquire OAuth token if required.

        Args:
            config: Configuration dictionary

        Returns:
            Token string or None

        Raises:
            HelpfulError: If token acquisition fails
        """
        if not self.require_token:
            logger.info("Token acquisition not required")
            return None

        try:
            # Extract OAuth config (hard-fail if missing when required)
            tenant_id = config["global"]["tenant-id"]
            client_id = config["global"]["client-id"]
            oauth_scope = config["global"]["oauth-scope"]
            client_secret = config["_client_secret"]  # From secrets

            if not self.oauth_client:
                self.oauth_client = OAuthClient(tenant_id=tenant_id, cache_tokens=True)

            token = self.oauth_client.get_client_credentials_token(
                client_id=client_id,
                client_secret=client_secret,
                scope=oauth_scope,
                tenant_id=tenant_id
            )

            logger.info("✅ Token acquired successfully")
            return token

        except KeyError as e:
            # Try fallback token from secrets
            fallback_token = config.get("_az_token")
            if fallback_token:
                logger.info("Using fallback token from secrets")
                return fallback_token

            raise HelpfulError(
                what_went_wrong=f"OAuth configuration incomplete: missing {e}",
                how_to_fix="Add OAuth settings to config or provide fallback token",
                example="Add 'az-token' to your secrets file for fallback"
            )
        except Exception as e:
            raise HelpfulError(
                what_went_wrong=f"Token acquisition failed: {e}",
                how_to_fix="Check OAuth configuration or add fallback token",
                example="Verify client-id, client-secret, and tenant-id"
            )

    def run(self, extra_args: Optional[List[ArgumentDefinition]] = None) -> Dict[str, Any]:
        """
        Main entry point - parse args, load config, get token.

        Args:
            extra_args: Optional additional arguments

        Returns:
            Complete configuration dictionary
        """
        # Parse arguments
        args = self.parse_arguments(extra_args)

        # Load configuration (always validates)
        config = self.load_configuration(args.org_id, args.env_type)

        # Inject extra arguments if provided
        if extra_args:
            for arg_def in extra_args:
                attr_name = arg_def.name.replace('-', '_')
                if hasattr(args, attr_name):
                    config[f"_{attr_name}"] = getattr(args, attr_name)

        # Acquire token if required
        if self.require_token:
            token = self.acquire_token(config)
            config["_token"] = token
        else:
            config["_token"] = None

        return config


def parse_args_and_load_config(description: str,
                               require_token: bool = True) -> Dict[str, Any]:
    """
    Parse arguments and load configuration - standard entry point.

    ALWAYS validates configuration against schema.
    No option to disable validation!

    Args:
        description: Script description
        require_token: Whether to acquire OAuth token

    Returns:
        Configuration dictionary with injected fields

    Example:
        config = parse_args_and_load_config("My script")
        # config['_org_id'], config['_env_type'], config['_token'] available
    """
    try:
        runner = ScriptRunner(description, require_token)
        return runner.run()

    except HelpfulError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def parse_custom_args_and_load_config(description: str,
                                      custom_args: Optional[List[ArgumentDefinition]] = None,
                                      require_token: bool = True) -> Dict[str, Any]:
    """
    Parse arguments with custom additions and load configuration.

    ALWAYS validates configuration - no escape hatch!

    Args:
        description: Script description
        custom_args: Additional argument definitions
        require_token: Whether to acquire OAuth token

    Returns:
        Configuration dictionary with all injected fields
    """
    try:
        runner = ScriptRunner(description, require_token)
        return runner.run(extra_args=custom_args)

    except HelpfulError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)