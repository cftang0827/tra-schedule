FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependencies file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN echo 5

# Copy the entire project into the container
COPY . .

# Set the Python module search path (for src/api structure)
ENV PYTHONPATH=/app/src

# Expose the FastAPI port
EXPOSE 8888

# Run the data loading script before starting the FastAPI app
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8888","--log-level", "warning"]
