FROM python:3.8-alpine 
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apk update && \
    apk upgrade && \
    apk add bash libc-dev libffi-dev postgresql-dev gcc python3-dev musl-dev 
RUN apk add build-base
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt 
COPY . .



