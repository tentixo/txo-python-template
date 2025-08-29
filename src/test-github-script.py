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

from utils.logger import setup_logger
from utils.script_runner import parse_args_and_load_config
from utils.load_n_save import TxoDataHandler
from utils.api_factory import create_rest_api
from utils.exceptions import ApiOperationError

logger = setup_logger()
data_handler = TxoDataHandler()


def fetch_github_repos(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch top Python repositories from GitHub.
    
    Args:
        config: Configuration dictionary with injected fields
        
    Returns:
        List of repository dictionaries
    """
    # Create API client
    api = create_rest_api(config)
    
    # GitHub API endpoint
    url = "https://api.github.com/search/repositories"
    
    logger.info("Fetching top Python repositories from GitHub")
    
    try:
        # Note: GitHub API doesn't require auth for public data
        # but has rate limits (60 requests/hour without auth)
        response = api.get(
            url,
            params={
                "q": "language:python stars:>1000",
                "sort": "stars",
                "order": "desc",
                "per_page": 10
            }
        )
        
        # Extract repositories from response
        repos = response.get("items", [])
        
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
                "updated_at": repo.get("updated_at")
            })
        
        return simplified_repos
        
    except ApiOperationError as e:
        logger.error(f"Failed to fetch repositories: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return []


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
        logger.info(f"✅ Saved {len(repos)} repositories to: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return False


def main():
    """Main entry point demonstrating TXO patterns."""
    # Pattern: Standard configuration loading
    config = parse_args_and_load_config("Test GitHub API access")
    
    # Pattern: Configuration injection
    org_id = config["_org_id"]
    env_type = config["_env_type"]
    
    logger.info(f"Starting GitHub API test for {org_id}-{env_type}")
    
    # Add delay configuration if not present
    if "script-behavior" not in config:
        config["script-behavior"] = {}
    if "api-delay-seconds" not in config["script-behavior"]:
        config["script-behavior"]["api-delay-seconds"] = 1
    
    # Fetch repository data
    start_time = time.time()
    repos = fetch_github_repos(config)
    elapsed = time.time() - start_time
    
    logger.info(f"API call completed in {elapsed:.2f} seconds")
    
    # Save results
    if repos:
        success = save_results(config, repos)
        if success:
            logger.info("✅ Test completed successfully")
        else:
            logger.error("❌ Failed to save results")
    else:
        logger.warning("⚠️ No repositories fetched - check your internet connection")
    
    # Summary
    logger.info(f"Test complete for {org_id}-{env_type}")


if __name__ == "__main__":
    main()