FROM alpine:latest AS webapp-build
RUN apk add --update --no-cache \
    nodejs nodejs-npm
ADD ./webclient/package*.json /webclient/
WORKDIR /webclient
RUN npm install
ADD ./webclient .
RUN node_modules/webpack/bin/webpack.js --mode production

FROM nickgryg/alpine-pandas:3.7.2 AS venv-image
RUN apk add linux-headers
RUN pip3 install virtualenv
RUN virtualenv /opt/venv
ENV path="/opt/venv/bin:$PATH"
RUN pip3 install flask uwsgi
RUN pip3 install music21
RUN pip3 install grpcio grpcio-tools

FROM alpine:latest
RUN apk add --update --no-cache \
    python3-dev protobuf
COPY --from=venv-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/venv/lib/python3.7"
ADD conf/requirements.prod /requirements.txt
RUN apk add --update postgresql-dev
RUN pip3 install -r /requirements.txt --timeout 120
COPY ./flask /flask
COPY --from=webapp-build /webclient/src/search.html /flask/templates/search.html
WORKDIR /flask
CMD ["uwsgi", "--module", "wsgi", "--uwsgi-socket", "socket/uwsgi.sock", "--chmod-socket=666", "--workers", "3", "--vacuum", "--die-on-term", "--master"]
