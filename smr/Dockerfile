FROM cbsmr:latest

# Compile w2 alg
WORKDIR /cbsmr/smr/helsinki-ttwi
RUN make -B

WORKDIR /cbsmr/smr
RUN go get
RUN go build

ENTRYPOINT ./smr
