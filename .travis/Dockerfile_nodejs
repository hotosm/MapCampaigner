FROM amazonlinux
RUN curl --silent --location https://rpm.nodesource.com/setup_10.x | bash \
  && yum install -y nodejs gcc-c++ make git
CMD ["npm", "install", "."]
