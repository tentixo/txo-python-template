# src/try-me-script.py
"""
Try Me First! - Simple script to test TXO Python Template setup

This script demonstrates core TXO patterns using GitHub's public API.
No authentication or complex setup required - it just works!

Usage:
    python try-me-script.py <org_id> <env_type>

Example:
    python try-me-script.py demo test

What it does:
    1. Fetches top Python repositories from GitHub
    2. Saves results to output/demo-test-github_repos_{UTC}.json
    3. Demonstrates logging, error handling, and file I/O patterns

Perfect for:
    - Testing your development environment
    - Learning TXO patterns
    - Validating the template setup
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
import time
import requests

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.exceptions import ApiOperationError, HelpfulError

logger = setup_logger()
data_handler = TxoDataHandler()


def fetch_github_repos(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch top Python repositories from GitHub's public API.

    Args:
        config: Configuration dictionary with injected fields

    Returns:
        List of repository dictionaries

    Raises:
        ApiOperationError: If GitHub API request fails
    """
    # Create session for public API
    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"{config['_org_id']}-{config['_env_type']}-script"
    })

    # GitHub search API endpoint
    url = "https://api.github.com/search/repositories"
    
    logger.info("Fetching top Python repositories from GitHub...")

    try:
        # Get configured delay (hard fail if script-behavior exists but delay is missing)
        try:
            delay = config["script-behavior"]["api-delay-seconds"]
        except KeyError:
            delay = 1  # Default if entire script-behavior section is missing
            
        if delay > 0:
            logger.debug(f"Waiting {delay}s before API call")
            time.sleep(delay)

        # Get timeout (hard fail if global exists but timeout is missing)
        try:
            timeout = config["global"]["timeout-seconds"]
        except KeyError:
            timeout = 30  # Default if not in global section
            
        # Make the API request
        response = session.get(
            url,
            params={
                "q": "language:python stars:>1000",
                "sort": "stars",
                "order": "desc",
                "per_page": 10
            },
            timeout=timeout
        )

        # Check for rate limiting
        if response.status_code == 403:
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
            
            raise ApiOperationError(
                f"GitHub rate limit hit! Remaining: {remaining}, "
                f"Resets at: {reset_time}"
            )

        response.raise_for_status()
        
        data = response.json()
        repos = data["items"]  # Hard fail if 'items' key missing
        
        logger.info(f"Successfully fetched {len(repos)} repositories")

        # Extract and structure the data
        results = []
        for repo in repos:
            # Required fields (hard fail if missing)
            results.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "stars": repo["stargazers_count"],
                "language": repo["language"],
                "url": repo["html_url"],
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                # Optional fields (using get for these)
                "description": repo.get("description", "No description"),
                "topics": repo.get("topics", []),
                "license": repo.get("license", {}).get("name") if repo.get("license") else "No license"
            })

        return results

    except KeyError as e:
        logger.error(f"GitHub API response missing expected field: {e}")
        raise ApiOperationError(f"Invalid GitHub API response structure: missing {e}")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise ApiOperationError(f"GitHub API request failed: {e}")
    finally:
        session.close()


def save_results(config: Dict[str, Any], repos: List[Dict[str, Any]]) -> None:
    """
    Save repository data to output file.

    Args:
        config: Configuration dictionary
        repos: List of repository data

    Raises:
        HelpfulError: If save operation fails
    """
    if not repos:
        logger.warning("No repositories to save")
        return

    # Build output filename with TXO pattern
    utc_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    org_id = config["_org_id"]  # Hard fail if missing
    env_type = config["_env_type"]  # Hard fail if missing
    
    filename = f"{org_id}-{env_type}-github_repos_{utc_timestamp}.json"

    try:
        # Save using intelligent save (auto-detects JSON from extension)
        output_path = data_handler.save(repos, "output", filename, indent=2)
        logger.info(f"✅ Saved {len(repos)} repositories to: {output_path}")
        
        # Log file size for verification
        file_size = output_path.stat().st_size
        logger.debug(f"Output file size: {file_size:,} bytes")
        
    except Exception as e:
        logger.error(f"Save operation failed: {e}")
        raise HelpfulError(
            what_went_wrong=f"Could not save results to output/{filename}",
            how_to_fix="Check that output/ directory exists and is writable",
            example="Create the directory: mkdir output"
        )


def display_summary(repos: List[Dict[str, Any]], elapsed_time: float) -> None:
    """
    Display a summary of fetched repositories.

    Args:
        repos: List of repository data
        elapsed_time: Time taken for API call
    """
    logger.info("=" * 60)
    logger.info("GitHub API Test - Summary")
    logger.info("=" * 60)
    logger.info(f"Total repositories fetched: {len(repos)}")
    logger.info(f"API call duration: {elapsed_time:.2f} seconds")
    logger.info("")
    logger.info("Top 3 Python repositories by stars:")
    
    for i, repo in enumerate(repos[:3], 1):
        logger.info(f"  {i}. {repo['full_name']}")
        logger.info(f"     ⭐ Stars: {repo['stars']:,}")
        logger.info(f"     📝 {repo['description'][:70]}...")
        logger.info("")
    
    logger.info("=" * 60)


def main():
    """Main entry point demonstrating TXO patterns."""
    # Load configuration WITHOUT token (public API doesn't need auth)
    config = parse_args_and_load_config(
        "Try Me Script - Test TXO Template with GitHub API",
        require_token=False  # No authentication needed
    )

    # Extract org and env (hard fail if missing)
    org_id = config["_org_id"]
    env_type = config["_env_type"]
    
    logger.info(f"🚀 Starting Try-Me script for {org_id}-{env_type}")
    
    # Check for configuration
    if "script-behavior" in config:
        logger.debug("Using script-behavior configuration")
    else:
        logger.info("Using default settings (no script-behavior config found)")

    try:
        # Time the API call
        start_time = time.time()
        repos = fetch_github_repos(config)
        elapsed = time.time() - start_time
        
        # Save the results
        save_results(config, repos)
        
        # Display summary
        display_summary(repos, elapsed)
        
        logger.info(f"✅ Try-Me script completed successfully for {org_id}-{env_type}")
        
    except ApiOperationError as e:
        logger.error(f"❌ API Error: {e}")
        logger.error("\nPossible causes:")
        logger.error("  1. No internet connection")
        logger.error("  2. GitHub API is temporarily down")
        logger.error("  3. Hit rate limit (wait a few minutes)")
        raise
        
    except HelpfulError:
        # Re-raise to let script_runner handle the display
        raise
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HelpfulError(
            what_went_wrong=f"Script failed unexpectedly: {e}",
            how_to_fix="Check the logs for details or run with --debug",
            example="python try-me-script.py demo test --debug"
        )


if __name__ == "__main__":
    import sys
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Script interrupted by user")
        sys.exit(130)
    except HelpfulError:
        # HelpfulError message already logged
        sys.exit(1)
    except Exception:
        # Unexpected errors already logged with traceback
        sys.exit(1)
