FROM python:latest

WORKDIR /app

COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN make w-cffi --directory helsinki-ttwi/
RUN pip install -e helsinki-ttwi/

EXPOSE 80

ENV FLASK_APP=./flask/app.py

CMD ["flask run"]
