FROM python:3.10-alpine
ARG USERNAME=app
ARG USER_UID=10000
ARG USER_GID=$USER_UID
RUN addgroup -g $USER_GID $USERNAME && adduser -u $USER_UID -G $USERNAME -D $USERNAME
USER $USERNAME
WORKDIR /app
COPY --chown=$USERNAME:$USERNAME requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY --chown=$USERNAME:$USERNAME . .
CMD ["python", "main.py"]
EXPOSE 22334
