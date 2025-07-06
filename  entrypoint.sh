#!/bin/sh
set -e
exec rasa run --enable-api --cors "*" -p "${PORT:-5005}"