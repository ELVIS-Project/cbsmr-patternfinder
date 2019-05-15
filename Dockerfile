FROM alpine:latest

ENV GOPATH /go
ENV GOBIN /gobin

RUN apk add --update --no-cache \
		git make libtool autoconf automake build-base \
		postgresql-dev \ 
		musl-dev linux-headers \
		python3 python3-dev \
		nodejs nodejs-npm \
		go \
		nginx

WORKDIR /cbsmr

# Cache the python deps
ADD ./conf/requirements.prod ./conf/requirements.prod
RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r conf/requirements.prod --timeout 120

# Cache webclient deps
ADD ./webclient/package*.json ./webclient/
WORKDIR /cbsmr/webclient
RUN npm install

# Do the rest
WORKDIR /cbsmr
ADD . .
RUN pip3 install .
RUN git submodule update --init --recursive
