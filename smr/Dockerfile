FROM cbsmr:latest

# Compile w2 alg
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make build/libw2.so

WORKDIR /cbsmr/smr
RUN GO111MODULE=off go get
RUN GO111MODULE=off go build

ENTRYPOINT ./smr
