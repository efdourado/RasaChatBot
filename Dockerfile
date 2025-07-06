FROM rasa/rasa:3.6.10

WORKDIR /app
COPY . .

RUN pip install -r actions/requirements.txt

RUN rasa train