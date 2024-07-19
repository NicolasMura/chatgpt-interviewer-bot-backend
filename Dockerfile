# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /

# Copy the requirements file into the container at /app
COPY requirements.txt /

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME=ob-sample-fast-api-docker

# Use the secret to set the environment variables
RUN --mount=type=secret,id=OPEN_AI_KEY \
  --mount=type=secret,id=OPEN_AI_ORG \
  --mount=type=secret,id=ELEVENLABS_KEY \
   export OPEN_AI_KEY=$(cat /run/secrets/OPEN_AI_KEY) && \
   export OPEN_AI_ORG=$(cat /run/secrets/OPEN_AI_ORG) && \
   export ELEVENLABS_KEY=$(cat /run/secrets/ELEVENLABS_KEY)

# Set the maintainer label
LABEL maintainer="Nicolas MURA <contact@nicolasmura.fr>"

# Run main.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# uvicorn main:app --host 0.0.0.0 --port $PORT