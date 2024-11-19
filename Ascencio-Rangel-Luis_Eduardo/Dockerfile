FROM ubuntu:latest

RUN apt-get update && \
    apt install -y openssh-server && \
    mkdir /var/run/sshd

RUN apt install -y \
    file \
    exiftool \
    ssdeep \
    git \
    build-essential \
    python3-pip \
    python3-venv \
    python3

RUN git clone https://github.com/radareorg/radare2 &&\
    cd radare2 ; sys/install.sh

RUN useradd -m admin && echo "admin:admin" | chpasswd && \
    mkdir -p /home/admin/.ssh && \
    chown -R admin:admin /home/admin/.ssh

RUN python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install --upgrade pip

WORKDIR $HOME

COPY ./staticLab/requirements.txt .

# Install requirements in the virtual environment
RUN /opt/venv/bin/pip install -r requirements.txt

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo "StrictHostKeyChecking no" >> /etc/ssh/ssh_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]