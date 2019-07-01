FROM cbsmr:latest

# Compile w2 alg
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make -B

WORKDIR /cbsmr/smr
RUN GO111MODULE=off go get
RUN GO111MODULE=off go build

ENTRYPOINT ./smr
