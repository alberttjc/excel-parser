# Use official Python runtime as a parent image
FROM python:3.13-slim-bookworm

# Set work directory
WORKDIR /app

# Install uv
RUN pip install uv && uv --version

# Copy all project files and directories
COPY . .
# Install python dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
