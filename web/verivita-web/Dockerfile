FROM ysihaoy/scala-play:2.12.2-2.6.0-sbt-0.13.15
WORKDIR /root/app
# caching dependencies
COPY ["build.sbt", "/tmp/build/"]
COPY ["project/plugins.sbt", "project/build.properties", "/tmp/build/project/"]
RUN apk update
RUN apk add --update nodejs
RUN npm install -g elm
RUN apk add --update python 
RUN apk add --update python-dev
RUN apk add --update py-pip
RUN apk add --update g++
RUN apk add --update make

RUN cd /tmp/build && \
 sbt compile && \
 sbt test:compile && \
 rm -rf /tmp/build

RUN pip install protobuf
RUN pip install ply
RUN pip install pysmt
RUN yes | pysmt-install --z3
RUN pip install jep



ENV VERIVITA_MOCK true

# copy code
COPY . /root/app/
WORKDIR /root/app
#RUN sbt compile && sbt test:compile

EXPOSE 9000
#CMD ["sleep","9999"]
#CMD ["echo", "container start"]
#CMD ["sbt", "dist"]
#CMD ["unzip", "/root/app/target/universal/play-elm-example-1.0-SNAPSHOT.zip"]
#CMD ["/root/app/play-elm-example-1.0-SNAPSHOT/bin/play-elm-example"]
#CMD ["echo", "container command complete"]

#block exit of docker container
CMD ["sh", "dockerstart.sh"] 
