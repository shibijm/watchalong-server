FROM python:3.10-alpine
ARG USERNAME=app
ARG USER_UID_GID=10000
RUN addgroup -g $USER_UID_GID $USERNAME && adduser -u $USER_UID_GID -G $USERNAME -D $USERNAME
USER $USERNAME
WORKDIR /app
COPY --chown=$USERNAME:$USERNAME requirements.txt .
RUN pip --no-cache-dir install -U -r requirements.txt
COPY --chown=$USERNAME:$USERNAME . .
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "main.py"]
EXPOSE 22334
