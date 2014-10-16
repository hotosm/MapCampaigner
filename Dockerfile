#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM ubuntu:trusty
MAINTAINER Tim Sutton<tim@kartoza.com>

RUN  export DEBIAN_FRONTEND=noninteractive
ENV  DEBIAN_FRONTEND noninteractive
RUN  dpkg-divert --local --rename --add /sbin/initctl
#RUN  ln -s /bin/true /sbin/initctl

# Use local cached debs from host (saves your bandwidth!)
# Change ip below to that of your apt-cacher-ng host
# Or comment this line out if you do not with to use caching
ADD 71-apt-cacher-ng /etc/apt/apt.conf.d/71-apt-cacher-ng

RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main universe" > /etc/apt/sources.list
RUN apt-get -y update
RUN apt-get -y install ca-certificates rpl pwgen

#-------------Application Specific Stuff ----------------------------------------------------

# Next line a workaround for https://github.com/dotcloud/docker/issues/963
RUN apt-get install -y tar \
   git \
   curl \
   nano \
   wget \
   dialog \
   net-tools \
   build-essential
# Install pip's dependency: setuptools:
apt-get install -y python python-dev python-distribute python-pip

ADD requirements.txt
RUN pip install -r requirements.txt
ADD server.py
ADD reporter /reporter

# Open port 80 so linked containers can see them
EXPOSE 8080


USER postgres
CMD ["python", "server.py"]
