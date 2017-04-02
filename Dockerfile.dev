#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.6
MAINTAINER Tim Sutton<tim@kartoza.com>

RUN  export DEBIAN_FRONTEND=noninteractive
ENV  DEBIAN_FRONTEND noninteractive
RUN  dpkg-divert --local --rename --add /sbin/initctl
#RUN  ln -s /bin/true /sbin/initctl

# Use local cached debs from host (saves your bandwidth!)
# Change ip below to that of your apt-cacher-ng host
# Or comment this line out if you do not with to use caching
ADD 71-apt-cacher-ng /etc/apt/apt.conf.d/71-apt-cacher-ng

RUN apt-get -y update
RUN apt-get -y install osm2pgsql

ADD requirements-dev.txt /requirements.txt
RUN pip install -r requirements.txt

ADD runserver.py /runserver.py
# we will use a volume rather
#ADD reporter /reporter

EXPOSE 5000

CMD ["python", "runserver.py"]
