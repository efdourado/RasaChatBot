FROM rasa/rasa:3.6.10-full

COPY . .

USER root

RUN rasa train

USER rasa

ENTRYPOINT ["/bin/sh", "-c"]

CMD ["rasa run --enable-api --cors \"*\" --debug -p $PORT"]