FROM rasa/rasa:3.6.10-full

COPY . .

USER root

RUN pip install --no-cache-dir -r actions/requirements.txt

RUN rasa train

USER rasa