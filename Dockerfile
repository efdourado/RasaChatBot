FROM rasa/rasa:3.6.10-full

COPY . .

USER root

RUN rasa train

USER rasa

ENTRYPOINT [ "/bin/sh", "-c", "rasa run --enable-api --cors \"*\" --port $PORT" ]