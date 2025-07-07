FROM rasa/rasa:3.6.10-full

COPY . .

USER root

RUN rasa train

USER rasa

CMD ["/bin/sh", "-c", "rasa run --enable-api --cors '*' --debug -p ${PORT:-10000}"]