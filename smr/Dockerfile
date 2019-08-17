FROM alpine:latest AS helsinki-build
RUN apk add --update --no-cache \
    make build-base
WORKDIR /cbsmr
ADD ./smr/helsinki-ttwi ./smr/helsinki-ttwi
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make build/libw2.so

FROM alpine:latest AS smr-build
ENV GOPATH /go
ENV GOBIN /go/bin
ENV PATH $PATH:$GOBIN
RUN apk add --update --no-cache \
    libtool build-base \
    musl-dev linux-headers \
    make git go protobuf
RUN go get -u google.golang.org/grpc
WORKDIR /cbsmr
ADD ./Makefile ./Makefile
ADD ./proto ./proto
RUN go get -u github.com/golang/protobuf/protoc-gen-go
RUN make proto/smr.pb.go
ADD ./smr /cbsmr/smr
WORKDIR /cbsmr/smr
COPY --from=helsinki-build /cbsmr/smr/helsinki-ttwi/build/libw2.so /cbsmr/smr/helsinki-ttwi/build/libw2.so
RUN GO111MODULE=off go get
RUN GO111MODULE=off go build

FROM alpine:latest AS smr
COPY --from=helsinki-build /cbsmr/smr/helsinki-ttwi/build/libw2.so /cbsmr/smr/helsinki-ttwi/build/libw2.so
COPY --from=smr-build /cbsmr/smr/smr /cbsmr/smr/smr
ENTRYPOINT /cbsmr/smr/smr
