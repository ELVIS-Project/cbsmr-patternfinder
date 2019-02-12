FROM python:latest

WORKDIR /app

COPY . .

RUN pip3 install pipenv
RUN pipenv install

EXPOSE 80

ENV FLASK_APP=./flask/app.py

CMD ["flask run"]