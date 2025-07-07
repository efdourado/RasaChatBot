FROM rasa/rasa:3.6.10-full

COPY . .

USER root
RUN rasa train
USER rasa

CMD rasa run --enable-api --cors "*" --debug --port ${PORT}