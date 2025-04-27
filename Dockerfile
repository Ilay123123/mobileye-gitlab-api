FROM alpine:3.18

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Create app directory
WORKDIR /app

# Create a non-root user to run the application
RUN adduser -D appuser

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gitlab_util.py .
COPY app.py .

# Change ownership of the application files
RUN chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Define health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:5000/health || exit 1

# Expose port for the service
EXPOSE 5000

# Run the application
CMD ["python3", "app.py"]