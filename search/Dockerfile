FROM python:latest

WORKDIR /app

COPY . .

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN pip install -e helsinki-ttwi/
RUN pip install -e ./
RUN make w-cffi --directory helsinki-ttwi/

EXPOSE 80

ENV FLASK_APP=./flask/app.py

CMD ["flask/app.py"]
