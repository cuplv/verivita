FROM postgres:10.4
WORKDIR /home/muse
COPY . /home/muse
RUN apt-get update
RUN apt-get install -y openssh-server vim
RUN mkdir /var/run/sshd
RUN chmod 0755 /var/run/sshd
RUN useradd muse
RUN groupadd admin
RUN usermod -a -G admin muse
RUN mkdir -p /home/muse
RUN chown -R muse:muse /home/muse
CMD ["sleep","99999"]
