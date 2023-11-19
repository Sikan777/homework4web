FROM python:3.11.6

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . .


EXPOSE 3000

CMD [ "python", "main.py"]

