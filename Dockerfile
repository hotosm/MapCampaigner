#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:2.7.8
MAINTAINER Tim Sutton<tim@kartoza.com>

RUN  export DEBIAN_FRONTEND=noninteractive
ENV  DEBIAN_FRONTEND noninteractive
RUN  dpkg-divert --local --rename --add /sbin/initctl
#RUN  ln -s /bin/true /sbin/initctl

# Use local cached debs from host (saves your bandwidth!)
# Change ip below to that of your apt-cacher-ng host
# Or comment this line out if you do not with to use caching
ADD 71-apt-cacher-ng /etc/apt/apt.conf.d/71-apt-cacher-ng

ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt
ADD server.py /server.py
ADD reporter /reporter

RUN apt-get -y update
RUN apt-get -y install postgis
# Open port 80 so linked containers can see them
EXPOSE 8080

CMD ["python", "server.py"]
