# Use the official Rasa image
FROM rasa/rasa:3.6.10-full

# Copy all your project files into the container
COPY . .

# Switch to the root user to have permissions to train
USER root

# Train the model when the image is built
RUN rasa train

# Switch back to the non-privileged 'rasa' user for security
USER rasa

# Override the base image's ENTRYPOINT completely.
# We tell Docker to start a shell and execute our command string.
# The shell will correctly expand the $PORT environment variable.
ENTRYPOINT [ "/bin/sh", "-c", "rasa run --enable-api --cors \"*\" --port $PORT" ]