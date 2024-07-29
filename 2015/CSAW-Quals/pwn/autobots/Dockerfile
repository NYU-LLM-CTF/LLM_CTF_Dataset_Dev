FROM ubuntu:14.04
MAINTAINER Steven
LABEL Description="CSAW 2015-Q: Autobots" VERSION='1.0'
# Update
# RUN apt-get update -y && apt-get -y upgrade && apt-get install -y python build-essential gcc
ARG PYTHON_VERSION=2.7.9
RUN apt-get update \
  && apt-get install -y wget gcc make openssl libffi-dev libgdbm-dev libsqlite3-dev libssl-dev zlib1g-dev \
  && apt-get clean

WORKDIR /tmp/

RUN wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz \
  && tar --extract -f Python-$PYTHON_VERSION.tgz \
  && cd ./Python-$PYTHON_VERSION/ \
  && ./configure --with-ensurepip=install --enable-optimizations --prefix=/usr/local \
  && make && make install \
  && cd ../ \
  && rm -r ./Python-$PYTHON_VERSION*

RUN wget https://bootstrap.pypa.io/pip/2.7/get-pip.py \
  && python get-pip.py

# Files
RUN mkdir -p /root/autobots
ADD autobots.py /root/autobots
WORKDIR /root/autobots
# Execute
ENTRYPOINT ["python", "autobots.py"]
EXPOSE 8888