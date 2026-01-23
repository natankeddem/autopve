FROM python:3.12-slim-trixie

RUN echo "**** install runtime dependencies ****"
RUN apt update
RUN apt install -y \
    openssh-client

ADD requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

WORKDIR /app
ADD . /app
RUN mkdir -p /app/logs

RUN chmod 777 /app/resources/docker-entrypoint.sh

EXPOSE 8080
ENV PYTHONUNBUFFERED True

ENTRYPOINT ["/app/resources/docker-entrypoint.sh"]
CMD ["python", "main.py"]
