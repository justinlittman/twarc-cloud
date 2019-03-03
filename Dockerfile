FROM python:3.7-alpine

# Required for psutils
RUN apk add --no-cache build-base linux-headers

RUN mkdir /opt/twarc-cloud
WORKDIR /opt/twarc-cloud

COPY requirements.txt /opt/twarc-cloud/
RUN pip install -r requirements.txt

COPY . /opt/twarc-cloud/
ENTRYPOINT ["python3", "tweet_harvester.py"]