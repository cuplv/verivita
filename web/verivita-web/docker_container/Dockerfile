FROM ubuntu:16.04
WORKDIR /home/muse
COPY . /home/muse/
RUN apt-get update
#RUN apt-get install -y openssh-server vim emacs gcc make sudo curl python2.7
RUN apt-get install -y openssh-server vim python2.7
RUN mkdir /var/run/sshd
RUN chmod 0755 /var/run/sshd
RUN useradd muse
RUN groupadd admin
RUN usermod -a -G admin muse
RUN mkdir -p /home/muse
RUN chown -R muse:muse /home/muse
RUN apt-get install -y python-pip 
#RUN pip install --upgrade pip #left out because failure https://github.com/pypa/pip/issues/5240
RUN pip install six
RUN pip install ply
RUN pip install protobuf
#RUN apt-get install -y python-six
#RUN apt-get install -y python-ply
#RUN apt-get install -y python-protobuf
RUN yes | python /home/muse/pysmt/install.py --z3
ENV PYTHONPATH "/root/.smt_solvers/python-bindings-2.7:/home/muse/cbverifier:/home/muse/pysmt:/home/muse"
ENV JAVA_HOME "/usr/lib/jvm/java-8-openjdk-amd64"
ENV TRACE_DIR "/home/muse/testTrace"
ENV LD_LIBRARY_PATH "/usr/local/lib/python2.7/dist-packages/jep"
RUN apt-get install -y openjdk-8-jdk-headless
RUN pip install jep
#TODO




EXPOSE 9000
# overwrite this with 'CMD []' in a dependent Dockerfile
CMD ["sleep", "9999"]


#FROM ysihaoy/scala-play:2.12.2-2.6.0-sbt-0.13.15
#WORKDIR /root/app
## caching dependencies
#COPY ["build.sbt", "/tmp/build/"]
#COPY ["project/plugins.sbt", "project/build.properties", "/tmp/build/project/"]
#RUN apk update
#RUN apk add --update nodejs
#RUN npm install -g elm
#RUN apk add --update python 
#RUN apk add --update python-dev
#RUN apk add --update py-pip
#RUN apk add --update g++
#RUN apk add --update make
#RUN apk add openrc
#RUN apk add openssh
#
#
#RUN cd /tmp/build && \
# sbt compile && \
# sbt test:compile && \
# rm -rf /tmp/build
#
#RUN pip install protobuf
#RUN pip install ply
#RUN pip install pysmt
#RUN yes | pysmt-install --z3
#RUN pip install jep
#
#
#
#ENV VERIVITA_MOCK true
#
## copy code
#COPY . /root/app/
#WORKDIR /root/app
##RUN sbt compile && sbt test:compile
#
#EXPOSE 9000
##CMD ["sleep","9999"]
##CMD ["echo", "container start"]
##CMD ["sbt", "dist"]
##CMD ["unzip", "/root/app/target/universal/play-elm-example-1.0-SNAPSHOT.zip"]
##CMD ["/root/app/play-elm-example-1.0-SNAPSHOT/bin/play-elm-example"]
##CMD ["echo", "container command complete"]
#
##block exit of docker container
#CMD ["sh", "dockerstart.sh"] 


#Pysmt old version install
#git clone git@github.com:pysmt/pysmt.git
#git checkout v0.6.1
#python install.py --z3
