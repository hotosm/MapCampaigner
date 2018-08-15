FROM amazonlinux:latest
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py
CMD ["pip", "install", "-r", "requirements.txt", "-t", "/dependencies"]


