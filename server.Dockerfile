FROM pytorch/pytorch:2.7.0-cuda11.8-cudnn9-runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8080
ENV MODEL_CHECKPOINT=/app/model_checkpoint.pt

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080"]