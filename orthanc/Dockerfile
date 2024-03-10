FROM orthancteam/orthanc


# Set environment variables
RUN apt-get update && apt install -y python3-venv
RUN python3 -m venv /.venv

RUN /.venv/bin/pip install pydicom requests
ENV PYTHONPATH=/.venv/lib64/python3.11/site-packages/

# Set the working directory to /app
WORKDIR /scripts

# Copy the current directory contents into the container at /scripts
COPY . /scripts
