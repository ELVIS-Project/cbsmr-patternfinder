FROM cbsmr:latest

WORKDIR /cbsmr/webclient
RUN node_modules/webpack/bin/webpack.js --mode production

WORKDIR /cbsmr/flask

CMD ["uwsgi", "--module", "wsgi", "--uwsgi-socket", "socket/uwsgi.sock", "--chmod-socket=666", "--workers", "3", "--vacuum", "--die-on-term", "--master"]
