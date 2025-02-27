FROM orthancteam/orthanc


# Set environment variables
RUN apt-get update && apt install -y python3-venv
RUN python3 -m venv /.venv

RUN /.venv/bin/pip install pydicom requests
ENV PYTHONPATH=/.venv/lib64/python3.11/site-packages/

# set locales
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8

ENV LANG en_US.UTF-8 

# Set the working directory to /app
WORKDIR /scripts

# Copy the current directory contents into the container at /scripts
COPY . /scripts


ARG UIG
ARG GID

RUN mkdir /automation_output
RUN chown -R $UID /automation_output
VOLUME /automation_output
RUN mkdir /automation_scripts
RUN chown -R $UID /automation_scripts
VOLUME /automation_scripts
USER $UID
