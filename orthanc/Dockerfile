FROM orthancteam/orthanc

RUN pip3 install pydicom
RUN mkdir -p /scripts
RUN mkdir -p /output
# COPY orthanc.json /etc/orthanc/
COPY *.py /scripts/
