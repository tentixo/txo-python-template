# utils/concurrency.py
import concurrent.futures
import argparse
from typing import List, Any, Callable, Dict, Tuple, Union
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from utils.api_helpers import SoapAPI, RestAPI

logger = setup_logger()

# Centralize the Business Central base URLs
SOAP_BASE_URL = "https://api.businesscentral.dynamics.com/v2.0"
REST_BASE_URL = "https://api.businesscentral.dynamics.com/v2.0"


def run_parallel_environments(environments: List[Any],
                              process_func: Callable[[Any], bool]) -> bool:
    """
    Run processing of environments concurrently.

    Args:
        environments (List[Any]): A list of environment configurations.
        process_func (Callable[[Any], bool]): A function that processes a single environment
            and returns a boolean indicating success.

    Returns:
        bool: True if all environments were processed successfully, False otherwise.
    """
    all_success = True
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_env = {
            executor.submit(process_func, env): env["id"] for env in environments
        }
        for future in concurrent.futures.as_completed(future_to_env):
            env_id = future_to_env[future]
            try:
                env_success = future.result()
                logger.info(f"Environment {env_id} processed with success: {env_success}")
                all_success = all_success and env_success
            except Exception as e:
                logger.error(f"Error processing environment {env_id}: {e}", exc_info=True)
                all_success = False
    return all_success


def _parse_args_and_load_config(description: str) -> Tuple[str, str, Dict[str, Any], ConfigLoader]:
    """
    Parse command line arguments and load configuration.

    Args:
        description: Description for the argument parser

    Returns:
        Tuple containing:
        - org_id: Organization ID
        - env_type: Environment type
        - config: Loaded configuration with additional keys
        - config_loader: ConfigLoader instance for further operations
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("org_id", help="Organization ID (e.g., 'txo')")
    parser.add_argument("env_type", help="Environment type (e.g., 'test', 'prod')")
    args = parser.parse_args()

    # Load configuration and secrets
    config_loader = ConfigLoader(args.org_id, args.env_type)
    config = config_loader.load()

    # Store org_id and env_type in config for convenience
    config["_org_id"] = args.org_id
    config["_env_type"] = args.env_type

    return args.org_id, args.env_type, config, config_loader


def run_script(script_name: str,
               env_processor: Callable[[Dict[str, Any], str, Union[SoapAPI, RestAPI], Dict[str, Any], int], bool],
               description: str,
               success_message: str,
               failure_message: str,
               use_rest_api: bool = False,
               api_delay: int = 60) -> None:
    """
    Run a Business Central script with standard argument parsing, config loading,
    and parallel environment processing. Can use either RestAPI or SoapAPI.

    Args:
        script_name (str): Name of the script (for logging)
        env_processor (Callable): Function that processes a single environment
        description (str): Description for the argparse help text
        success_message (str): Message to log on overall success
        failure_message (str): Message to log on overall failure
        use_rest_api (bool): Whether to use RestAPI instead of SoapAPI (default: False)
        api_delay (int): Timeout for API calls in seconds (default: 60)
    """
    org_id, env_type, config, config_loader = _parse_args_and_load_config(description)

    logger.info(f"Starting {script_name} for {org_id} in {env_type} environment")

    # Get standard config values
    tenant_id = config["global"]["tenant-id"]

    # Store token in config for convenience
    token = config_loader.get_token()
    config["_token"] = token

    # Create appropriate API client based on use_rest_api flag
    if use_rest_api:
        # Using the new token-based initialization for RestAPI
        api_client = RestAPI(token, timeout=api_delay)
    else:
        api_client = SoapAPI(token, timeout=api_delay)

    environments = config["bc-environments"][env_type]

    def process_env_wrapper(env: Dict[str, Any]) -> bool:
        """Wrapper to provide additional context to the environment processor"""
        # Pass the appropriate timeout to the processor function
        # Rate-limiting delay is always passed regardless of API type
        return env_processor(env, tenant_id, api_client, config, api_delay)

    # Process environments concurrently
    all_success = run_parallel_environments(environments, process_env_wrapper)

    if all_success:
        logger.info(success_message)
    else:
        logger.warning(failure_message)


def load_bc_config(org_id: str, env_type: str) -> Tuple[Dict[str, Any], str, int, str, SoapAPI]:
    """
    Load Business Central configuration and create a SOAP API client.

    Args:
        org_id: Organization identifier
        env_type: Environment type (test, prod, etc.)

    Returns:
        Tuple containing:
        - config: The full configuration dictionary
        - tenant_id: The tenant ID
        - api_delay: API delay in seconds
        - token: The API token
        - soap_api: Initialized SoapAPI client
    """
    config_loader = ConfigLoader(org_id, env_type)
    config = config_loader.load()
    tenant_id = config["global"]["tenant-id"]
    api_delay = config["global"].get("api_delay_seconds", 2)
    token = config_loader.get_token()
    soap_api = SoapAPI(token, timeout=60)

    return config, tenant_id, api_delay, token, soap_api