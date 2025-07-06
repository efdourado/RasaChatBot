FROM rasa/rasa:3.6.10-full

COPY . .

USER root

RUN pip install --no-cache-dir -r actions/requirements.txt

RUN rasa train

USER rasa


WORKDIR /app
COPY . .

EXPOSE 8080

COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]