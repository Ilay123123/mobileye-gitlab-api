# GitLab API Service

This project implements a service for interacting with GitLab API (Version 15.11) as part of the Mobileye DevOps-IT home assignment.

## Features

The service provides two main functionalities:

1. **Permission Management**: Grant or modify user permissions on GitLab groups or projects
2. **Item Retrieval**: Get all issues or merge requests created in a specific year

## Project Structure

- `gitlab_util.py` - Core functions that interact with GitLab API
- `app.py` - Flask application that exposes the functionality as REST endpoints
- `Dockerfile` - Container definition for running the service
- `requirements.txt` - Python dependencies

## API Endpoints

### Permission Management
```
POST /permission
```
Body:
```json
{
  "username": "gitlab_username",
  "target": "group_name_or_project_path",
  "role": "developer"
}
```
Valid roles: guest, reporter, developer, maintainer, owner

### Item Retrieval
```
GET /items?type=issues&year=2023
```
Parameters:
- `type`: Either "mr" (merge requests) or "issues"
- `year`: 4-digit year to filter by

### Health Check
```
GET /health
```

## Environment Variables

- `GITLAB_URL`: GitLab instance URL (default: "https://gitlab.com/")
- `GITLAB_TOKEN`: Your GitLab API token with appropriate permissions

## Running locally

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Set your GitLab token:
   ```
   export GITLAB_TOKEN="your_gitlab_token"
   ```

3. Run the application:
   ```
   python app.py
   ```

## Docker Deployment

1. Build the Docker image:
   ```
   docker build -t gitlab-api-service .
   ```

2. Run the container:
   ```
   docker run -p 5000:5000 -e GITLAB_TOKEN="your_gitlab_token" gitlab-api-service
   ```

## Using the Command Line Interface

The `gitlab_util.py` script can also be used directly from the command line:

```bash
# Modify permissions
python gitlab_util.py permission --username user123 --target my-group --role developer

# Get items by year
python gitlab_util.py items --type issues --year 2023
```

## Security Considerations

- The service runs as a non-root user inside the container
- GitLab token is passed as an environment variable rather than being hardcoded
- Input validation is implemented for all parameters