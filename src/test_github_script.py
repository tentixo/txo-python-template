# src/test_github_api.py
"""
Test script - Fetch public GitHub repository information

This script demonstrates TXO patterns using GitHub's public API.
No authentication required - works for everyone!

Usage:
    python test_github_api.py <org_id> <env_type>

Example:
    python test_github_api.py demo test

Output:
    Creates JSON file in output/ directory with GitHub repository data
    Format: {org_id}-{env_type}-github_repos_{UTC}.json
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
    Fetch top Python repositories from GitHub.

    Args:
        config: Configuration dictionary with injected fields

    Returns:
        List of repository dictionaries

    Raises:
        ApiOperationError: If GitHub API request fails
    """
    # For public APIs, use requests directly
    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": f"{config['_org_id']}-{config['_env_type']}-script"
    })

    # GitHub API endpoint
    url = "https://api.github.com/search/repositories"

    logger.info("Fetching top Python repositories from GitHub")

    try:
        # Apply rate limiting if configured
        delay = config.get("script-behavior", {}).get("api-delay-seconds", 1)
        if delay > 0:
            logger.debug(f"Applying {delay}s delay before API call")
            time.sleep(delay)

        # Make API request
        timeout = config.get("global", {}).get("timeout-seconds", 30)
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
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset', 'unknown')

            raise ApiOperationError(
                f"GitHub API rate limit exceeded. "
                f"Remaining: {rate_limit_remaining}, "
                f"Reset time: {rate_limit_reset}"
            )

        response.raise_for_status()

        data = response.json()
        repos = data.get("items", [])

        logger.info(f"Successfully fetched {len(repos)} repositories")

        # Extract relevant fields
        simplified_repos = []
        for repo in repos:
            simplified_repos.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count"),
                "language": repo.get("language"),
                "url": repo.get("html_url"),
                "created_at": repo.get("created_at"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
                "license": repo.get("license", {}).get("name") if repo.get("license") else None
            })

        return simplified_repos

    except requests.RequestException as e:
        logger.error(f"Failed to fetch repositories: {e}")
        raise ApiOperationError(f"GitHub API error: {e}")
    finally:
        session.close()


def save_results(config: Dict[str, Any], repos: List[Dict[str, Any]]) -> bool:
    """
    Save repository data to output file.

    Args:
        config: Configuration dictionary
        repos: List of repository data

    Returns:
        True if successful, False otherwise
    """
    if not repos:
        logger.warning("No data to save")
        return False

    # Pattern: Output file naming with UTC timestamp
    current_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    org_id = config["_org_id"]
    env_type = config["_env_type"]

    output_filename = f"{org_id}-{env_type}-github_repos_{current_utc}.json"

    try:
        # Save to output directory
        file_path = data_handler.save(repos, "output", output_filename)
        logger.info(f"Saved {len(repos)} repositories to: {file_path}")

        # Calculate and log file size
        file_size = file_path.stat().st_size
        logger.debug(f"Output file size: {file_size:,} bytes")

        return True

    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise HelpfulError(
            what_went_wrong=f"Failed to save results to output directory: {e}",
            how_to_fix="Ensure the output/ directory exists and is writable",
            example="Check file permissions or create the directory manually"
        )


def main():
    """Main entry point demonstrating TXO patterns."""
    # Pattern: Load config WITHOUT token for public API
    config = parse_args_and_load_config(
        "Test GitHub API access - Demonstrates TXO patterns with public API",
        require_token=False,  # No token needed for public API
        validate_config=False  # Don't require schema validation for test script
    )

    # Pattern: Configuration injection
    org_id = config["_org_id"]
    env_type = config["_env_type"]

    logger.info(f"Starting GitHub API test for {org_id}-{env_type}")

    # Log configuration status
    if config.get("script-behavior"):
        logger.debug("Script behavior configuration loaded")
    else:
        logger.warning("No script-behavior configuration found, using defaults")

    # Fetch repository data
    start_time = time.time()

    try:
        repos = fetch_github_repos(config)
        elapsed = time.time() - start_time

        logger.info(f"API call completed in {elapsed:.2f} seconds")

        # Save results
        if repos:
            success = save_results(config, repos)
            if success:
                logger.info("✅ Test completed successfully")

                # Log summary
                logger.info("=" * 50)
                logger.info("GitHub API Test Results")
                logger.info("=" * 50)
                logger.info(f"Organization: {org_id}")
                logger.info(f"Environment: {env_type}")
                logger.info(f"Repositories fetched: {len(repos)}")
                logger.info(f"Execution time: {elapsed:.2f}s")
                logger.info("=" * 50)

                # Display top 3 repositories
                logger.info("Top 3 Python repositories by stars:")
                for i, repo in enumerate(repos[:3], 1):
                    logger.info(f"{i}. {repo['full_name']} - ⭐ {repo['stars']:,}")
                    if repo.get('description'):
                        logger.info(f"   {repo['description'][:80]}...")

            else:
                logger.error("❌ Failed to save results")
        else:
            logger.warning("⚠️ No repositories fetched - check your internet connection")

    except ApiOperationError as e:
        logger.error(f"❌ Test failed: {e}")
        logger.error(f"API Error: {e}")
        logger.error("Possible causes:")
        logger.error("1. No internet connection")
        logger.error("2. GitHub API is down")
        logger.error("3. Rate limiting (if you've made many requests)")
        import sys
        sys.exit(1)

    except HelpfulError as e:
        # HelpfulError will be caught and displayed by parse_args_and_load_config
        logger.error(str(e))
        raise

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HelpfulError(
            what_went_wrong=f"Unexpected error occurred: {e}",
            how_to_fix="Check the debug log for more details",
            example="Run with --debug flag for detailed logging"
        )

    # Summary
    logger.info(f"Test complete for {org_id}-{env_type}")


if __name__ == "__main__":
    import sys

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(130)