from flask import Flask, request, jsonify
import gitlab_util  # Import your GitLab API script
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with usage instructions"""
    return jsonify({
        "service": "GitLab API Service",
        "endpoints": {
            "/health": "Health check endpoint",
            "/permission": "POST endpoint to modify user permissions",
            "/items": "GET endpoint to retrieve issues or merge requests by year"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/permission', methods=['POST'])
def permission():
    """Endpoint to modify user permissions"""
    # Get parameters from the request
    data = request.json
    if not data:
        logger.error("No JSON data provided in the request")
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400

    # Validate required parameters
    required_params = ['username', 'target', 'role']
    missing_params = [param for param in required_params if param not in data]
    if missing_params:
        error_msg = f"Missing required parameters: {', '.join(missing_params)}"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 400

    # Call the function
    logger.info(f"Modifying permission for user {data['username']} on {data['target']} to {data['role']}")
    result = gitlab_util.modify_permission(
        data['username'],
        data['target'],
        data['role']
    )

    # Return the result
    if result and result.get("status") == "success":
        return jsonify(result)
    else:
        # Return the error with status code 400
        return jsonify(result), 400

@app.route('/items', methods=['GET'])
def items():
    """Endpoint to get items by year"""
    # Get parameters from the request
    item_type = request.args.get('type')
    year = request.args.get('year')

    # Validate required parameters
    if not item_type:
        error_msg = "Missing required parameter: type"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 400
    if not year:
        error_msg = "Missing required parameter: year"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 400

    # Call the function
    logger.info(f"Retrieving {item_type} for year {year}")
    result = gitlab_util.get_items_by_year(item_type, year)

    # Return the result
    if result and result.get("status") == "success":
        return jsonify(result)
    else:
        # Return the error with status code 400
        return jsonify(result), 400

if __name__ == '__main__':
    # Log when the app starts
    logger.info("Starting GitLab API Service")
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)