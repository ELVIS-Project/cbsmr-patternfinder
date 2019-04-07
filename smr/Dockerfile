FROM grpc/go:latest

WORKDIR /cbsmr
ADD . .

RUN git submodule update --init ; \
		make proto

WORKDIR /cbsmr/smr
RUN go build

EXPOSE ${SMR_PORT}

ENTRYPOINT ./smr
