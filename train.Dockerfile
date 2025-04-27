FROM pytorch/pytorch:2.7.0-cuda11.8-cudnn9-runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git curl unzip gcc

WORKDIR /acetrace

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install -i /trex/aws-cli -b /usr/local/bin

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY init.sh .
RUN chmod +x init.sh

ENV PATH /opt/conda/bin:$PATH