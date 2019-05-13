FROM alpine:latest

ENV GOPATH /go
ENV GOBIN /gobin

RUN apk add --update --no-cache \
		git make libtool autoconf automake build-base \
		postgresql-dev \ 
		musl-dev linux-headers \
		python3 python3-dev \
		go \
		nginx

WORKDIR /cbsmr

# Cache the python deps
ADD ./conf/requirements.prod ./conf/requirements.prod
RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r conf/requirements.prod --timeout 120

# Do the rest
WORKDIR /cbsmr
ADD . .
RUN pip3 install .
RUN git submodule update --init --recursive
