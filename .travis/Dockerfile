FROM amazonlinux
RUN amazon-linux-extras install -y python3 && \
    pip3 install --user && \
    pip3 install --upgrade pip
CMD ["pip3", "install", "-r", "requirements.txt", "-t", "/dependencies"]


