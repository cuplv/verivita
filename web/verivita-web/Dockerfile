FROM ysihaoy/scala-play:2.12.2-2.6.0-sbt-0.13.15
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



#RUN apt-get install npm
#RUN apt-get install python2.7

ENV VERIVITA_MOCK true

# copy code
COPY . /root/app/
WORKDIR /root/app
#RUN sbt compile && sbt test:compile

EXPOSE 9000
CMD ["sleep","9999"]
#CMD ["sbt", "run"]
