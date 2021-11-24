FROM python:3.8.5

WORKDIR /code

# Install OpenJDK-11
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean;

RUN ["python", "-m", "pip", "install", "-r", "requirements.txt"]
