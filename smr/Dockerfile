#
FROM golang:1.12-alpine AS helsinki-build
RUN apk add --update --no-cache \
    make build-base
WORKDIR /cbsmr
ADD ./smr/helsinki-ttwi ./smr/helsinki-ttwi
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make build/libw2.so

#
FROM golang:1.12-alpine AS smr-build
ENV GOPATH /go
ENV GOBIN /go/bin
ENV PATH $GOBIN:$PATH
RUN apk add --update --no-cache \
		g++ git protobuf make
RUN go get -u google.golang.org/grpc
RUN go get -u github.com/golang/protobuf/protoc-gen-go
WORKDIR /cbsmr

ADD ./Makefile ./Makefile
ADD ./proto ./proto
RUN make proto/smr.pb.go

ADD ./smr /cbsmr/smr
WORKDIR /cbsmr/smr
RUN GO111MODULE=off go get
COPY --from=helsinki-build /cbsmr/smr/helsinki-ttwi/build/libw2.so /cbsmr/smr/helsinki-ttwi/build/libw2.so
RUN GO111MODULE=off go build

#
FROM golang:1.12-alpine AS smr
COPY --from=helsinki-build /cbsmr/smr/helsinki-ttwi/build/libw2.so /cbsmr/smr/helsinki-ttwi/build/libw2.so
COPY --from=smr-build /cbsmr/smr/smr /cbsmr/smr/smr
RUN mkdir /cbsmr/smr/bolt
ENTRYPOINT /cbsmr/smr/smr
