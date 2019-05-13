FROM cbsmr:latest

RUN apk add --update --no-cache nodejs nodejs-npm

WORKDIR /cbsmr/webclient
RUN npm install
RUN node_modules/webpack/bin/webpack.js

WORKDIR /cbsmr/flask

#CMD ["python3", "app.py"]
CMD ["uwsgi", "--module", "wsgi", "--uwsgi-socket", "socket/uwsgi.sock", "--workers", "3", "--vacuum", "--die-on-term", "--master"]
