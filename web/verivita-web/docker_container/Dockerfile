FROM ubuntu:16.04
WORKDIR /home/muse
COPY . /home/muse/
RUN apt-get update
RUN apt-get install -y openjdk-8-jdk-headless
RUN apt-get install -y openssh-server vim python2.7
RUN mkdir /var/run/sshd
RUN chmod 0755 /var/run/sshd
RUN useradd muse
RUN groupadd admin
RUN usermod -a -G admin muse
RUN mkdir -p /home/muse
RUN chown -R muse:muse /home/muse
ENV JAVA_HOME "/usr/lib/jvm/java-8-openjdk-amd64"
ENV VERIVITA_WEB_URL "http://127.0.0.1:5000"
ENV TRACEQUERY_WEB_URL "http://127.0.0.1:8080"


EXPOSE 9000
CMD ["/home/muse/vvweb-1.0-SNAPSHOT/bin/vvweb"]
