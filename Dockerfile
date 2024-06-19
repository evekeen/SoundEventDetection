FROM pytorch/pytorch:2.3.1-cuda11.8-cudnn8-runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git curl unzip gcc

WORKDIR /acetrace

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY init.sh .
RUN chmod +x init.sh

ENV PATH /opt/conda/bin:$PATH