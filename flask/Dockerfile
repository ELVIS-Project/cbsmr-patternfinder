### Website ###
FROM alpine:latest AS webapp-build
RUN apk add --update --no-cache \
    nodejs nodejs-npm
ADD ./webclient/package*.json /webclient/
WORKDIR /webclient
RUN npm install
ADD ./webclient .
RUN node_modules/webpack/bin/webpack.js --mode development

### Virtualenv ###
FROM python:3.7.4 AS venv-image
RUN pip3 install virtualenv
RUN virtualenv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip3 install flask uwsgi
RUN pip3 install music21
RUN pip3 install grpcio grpcio-tools
RUN pip3 install numpy pandas

### Flask ###
FROM python:3.7.4
COPY --from=venv-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /cbsmr

ADD ./Makefile .
ADD ./proto ./proto
RUN make proto/smr_pb2.py proto/smr_pb2_grpc.py

ADD ./flask/requirements.txt ./flask/requirements.txt
RUN pip3 install -r ./flask/requirements.txt

ADD setup.py .
RUN pip3 install -e .

ADD ./flask/ ./flask/
COPY --from=webapp-build /webclient/src/*.html /cbsmr/flask/templates/search.html
COPY --from=webapp-build /webclient/dist/*.js /cbsmr/flask/templates/search.js

WORKDIR /cbsmr/flask
CMD ["uwsgi", "--module", "wsgi", "--uwsgi-socket", "socket/uwsgi.sock", "--chmod-socket=666", "--workers", "3", "--vacuum", "--die-on-term", "--master"]
