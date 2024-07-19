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

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Set the maintainer label
LABEL maintainer="Nicolas MURA <contact@nicolasmura.fr>"

# Run main.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
# uvicorn main:app --host 0.0.0.0 --port $PORT