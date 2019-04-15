FROM cbsmr:latest

ENV GOPATH /go
ENV GOBIN /go/bin

WORKDIR /cbsmr/smr
RUN go get
RUN go build

ENTRYPOINT ./smr
