FROM alpine:latest

RUN apk add --update --no-cache \
		git make libtool autoconf automake build-base \
		postgresql-dev musl-dev \
		python3 python3-dev \
		go

WORKDIR /cbsmr

# Cache the python deps
ADD ./conf/requirements.prod ./conf/requirements.prod

RUN pip3 install --upgrade pip setuptools
RUN pip3 install -r conf/requirements.prod --timeout 60

ADD . .

RUN pip3 install .

# Compile w2 alg
RUN git submodule update --init --recursive
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make -B
WORKDIR /cbsmr


#RUN go get github.com/golang/protobuf/protoc-gen-go

#RUN git clone https://github.com/google/protobuf.git && \
#    cd protobuf && \
#    ./autogen.sh && \
#    ./configure && \
#    make && \
#    make install && \
#    ldconfig && \
#    make clean && \
#    cd .. && \
#    rm -r protobuf

# indexer: python, protobuf, python-grpc, make, pip, install reqs
# smr: golang, helsinki-ttwi
# flask: more python reqs
