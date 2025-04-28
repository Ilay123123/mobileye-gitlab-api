from requests.utils import quote
from datetime import datetime
import json
import requests
import re
import os
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_inputs(username=None, target=None, role=None, item_type=None, year=None):
    """Validate input parameters for both functions"""
    errors = []

    if username is not None and not username.strip():
        errors.append("Username cannot be empty")

    if target is not None and not target.strip():
        errors.append("Target (group/project) cannot be empty")

    if role is not None and role.lower() not in ROLE_MAPPING:
        errors.append(f"Invalid role: {role}. Valid roles are: {', '.join(ROLE_MAPPING.keys())}")

    if item_type is not None and item_type not in ["mr", "issues"]:
        errors.append(f"Invalid item type: {item_type}. Must be 'mr' or 'issues'")

    if year is not None:
        try:
            year = int(year)
            current_year = datetime.now().year
            if year < 2010 or year > current_year:
                errors.append(f"Invalid year: {year}. Must be between 2010 and {current_year}")
        except ValueError:
            errors.append(f"Year must be a valid integer, got '{year}'")

    # Check if token is set
    if not TOKEN:
        errors.append("GITLAB_TOKEN environment variable is not set")

    return errors

# Get configuration from environment variables
GITLAB_URL = os.environ.get("GITLAB_URL", "https://gitlab.com/")
# Make sure the URL ends with a slash
GITLAB_URL = GITLAB_URL.rstrip('/') + '/'
TOKEN = os.environ.get("GITLAB_TOKEN")
HEADERS = {"PRIVATE-TOKEN": TOKEN}

ROLE_MAPPING = {
    "guest": 10,
    "reporter": 20,
    "developer": 30,
    "maintainer": 40,
    "owner": 50  # Only for groups, not for projects
}

def modify_permission(username, target, role):
    """
    Modify user permissions on a GitLab project or group

    Args:
        username (str): The GitLab username
        target (str): The target group or project name
        role (str): The role to assign

    Returns:
        dict: JSON response on success, or error information on failure
    """
    # Validate inputs and return errors if any
    errors = validate_inputs(username=username, target=target, role=role)
    if errors:
        logger.error(f"Validation errors: {errors}")
        return {"status": "error", "errors": errors}

    # Check if role is 'owner' for a project (not supported)
    if "/" in target and role.lower() == "owner":
        logger.error("Owner role is not supported for projects")
        return {"status": "error", "message": "Owner role is not supported for projects"}

    try:
        # Get user ID
        logger.info(f"Looking up user ID for username: {username}")
        user_res = requests.get(
            f"{GITLAB_URL}api/v4/users?username={username}",
            headers=HEADERS,
            timeout=10
        )

        # Check response status
        if user_res.status_code != 200:
            error_msg = f"API request failed with status {user_res.status_code}: {user_res.text}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        users = user_res.json()

        # Determine if user exists
        if not users:
            error_msg = f"User '{username}' not found"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # Extract user ID
        user_id = users[0]["id"]
        logger.info(f"Found user ID {user_id} for username {username}")

        # Determine if target is a group or project
        if "/" in target:
            # It's a project
            endpoint = f"{GITLAB_URL}api/v4/projects/{requests.utils.quote(target, safe='')}/members"
            logger.info(f"Target '{target}' identified as a project")
        else:
            # It's a group
            endpoint = f'{GITLAB_URL}api/v4/groups/{target}/members'
            logger.info(f"Target '{target}' identified as a group")

        # Set up data for the API call
        data = {
            "user_id": user_id,
            "access_level": ROLE_MAPPING[role.lower()]
        }

        # Add or update the member
        logger.info(f"Attempting to add {username} to {target} with role {role}")
        response = requests.post(endpoint, json=data, headers=HEADERS)

        # Check if the target exists
        if response.status_code == 404:
            error_msg = f"Target '{target}' not found"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # If the user is already a member, update their access level
        if response.status_code == 409:  # 409 means conflict - user already exists
            logger.info(f"User {username} already exists in {target}, updating role")
            response = requests.put(f"{endpoint}/{user_id}", json=data, headers=HEADERS)

        # Check if the request was successful
        if response.status_code < 200 or response.status_code >= 300:
            error_msg = f"Failed to modify permission: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        logger.info(f"Successfully set {username}'s role to {role} on {target}")
        return {
            "status": "success",
            "message": f"Successfully set {username}'s role to {role} on {target}",
            "data": response.json()
        }

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        # Catch any other unexpected errors
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

ITEMS = ["mr", "issues"]
VALID_YEARS = list(range(2010, datetime.now().year + 1))

def get_items_by_year(item_type, year):
    """
    Get items (merge requests or issues) created in a specific year

    Args:
        item_type (str): Type of items to retrieve ('mr' or 'issues')
        year (int or str): Year to filter by

    Returns:
        dict: Filtered list of items with id, title, created_at, state, web_url, or error information
    """
    # Validate inputs and return errors if any
    errors = validate_inputs(item_type=item_type, year=year)
    if errors:
        logger.error(f"Validation errors: {errors}")
        return {"status": "error", "errors": errors}

    # Convert year to integer if it's a string
    try:
        year = int(year)
    except ValueError:
        error_msg = f"Error: year must be a 4-digit number, got '{year}'"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    # Format check & Check if year exists
    if not re.fullmatch(r"\d{4}", str(year)) or year not in VALID_YEARS:
        error_msg = f"Invalid year: {year}. Must be 4 digits and between 2010 and {datetime.now().year}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    # Create date range parameters
    created_after = f"{year}-01-01T00:00:00Z"
    created_before = f"{year}-12-31T23:59:59Z"
    logger.info(f"Retrieving {item_type} created between {created_after} and {created_before}")

    if item_type == "mr":
        # For merge requests
        endpoint = f"{GITLAB_URL}api/v4/merge_requests"
    else:
        # For issues
        endpoint = f"{GITLAB_URL}api/v4/issues"

    current_page = 1
    all_results = []

    while True:
        # Parameters for the API request
        params = {
            "created_after": created_after,
            "created_before": created_before,
            "per_page": 100,
            "page": current_page
        }

        logger.info(f"Requesting page {current_page} of {item_type}")
        response = requests.get(endpoint, params=params, headers=HEADERS)

        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f"Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        try:
            # Get data from current page
            page_data = response.json()
        except json.JSONDecodeError:
            error_msg = "Error: Invalid JSON response"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        # If no more data, break the loop
        if not page_data:
            logger.info(f"Found {len(all_results)} {item_type} from {year}")
            # Filter results to include only essential fields
            filtered_results = [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "created_at": item["created_at"],
                    "state": item["state"],
                    "web_url": item["web_url"]
                }
                for item in all_results
            ]
            return {
                "status": "success",
                "message": f"Retrieved {len(filtered_results)} {item_type} from {year}",
                "data": filtered_results
            }

        # Add data to the result list
        all_results.extend(page_data)
        logger.info(f"Added {len(page_data)} items from page {current_page}, total: {len(all_results)}")

        # Go to the next page
        current_page += 1

def main():
    """Command line interface for GitLab API functions"""
    parser = argparse.ArgumentParser(description='GitLab API Functions')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Subparser for modify_permission
    permission_parser = subparsers.add_parser('permission', help='Modify user permissions')
    permission_parser.add_argument('--username', required=True, help='GitLab username')
    permission_parser.add_argument('--target', required=True, help='Group or project path')
    permission_parser.add_argument('--role', required=True, choices=list(ROLE_MAPPING.keys()),
                                   help='Permission role to assign')

    # Subparser for get_items_by_year
    items_parser = subparsers.add_parser('items', help='Get issues or merge requests by year')
    items_parser.add_argument('--type', required=True, choices=['mr', 'issues'],
                              help='Type of items to retrieve')
    items_parser.add_argument('--year', required=True, type=int,
                              help='Year to filter by (4-digit year)')

    # Parse arguments
    args = parser.parse_args()

    # Execute command
    if args.command == 'permission':
        result = modify_permission(args.username, args.target, args.role)
        print(json.dumps(result, indent=2))
    elif args.command == 'items':
        result = get_items_by_year(args.type, args.year)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()