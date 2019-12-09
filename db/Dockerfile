FROM alpine:latest AS verovio
RUN apk add --update --no-cache \
    build-base cmake git
RUN git clone https://github.com/rism-ch/verovio.git
WORKDIR verovio/tools
RUN cmake . && make && make install/strip

FROM postgres:12

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update
RUN apt-get -y install python3 python3-pip postgresql-plpython3-12 libssl-dev libpq-dev libgmp-dev

RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install music21

ADD smrpy /smrpy
ADD proto /proto
RUN pip3 install -r /smrpy/requirements.txt
ADD setup.py .
RUN pip3 install -e .

ADD db/plpyext /db/plpyext
ADD db/sql /docker-entrypoint-initdb.d/ 
ENV PYTHONPATH=/db

COPY --from=verovio /usr/local/bin/verovio /usr/local/bin/verovio
COPY --from=verovio /usr/local/share/verovio /usr/local/share/verovio
