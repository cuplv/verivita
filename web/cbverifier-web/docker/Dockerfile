#Use an official Python runtime as a parent image
FROM ubuntu:16.04

# Set the working directory to /home/muse
WORKDIR /home/muse

# Install any needed packages specified in requirements.txt
#RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update
RUN apt-get install -y openssh-server vim gcc make sudo curl python2.7 python-pip sqlite3
RUN mkdir /var/run/sshd
RUN useradd muse
RUN groupadd admin
RUN usermod -a -G admin muse
RUN mkdir -p /home/muse
RUN chown -R muse:muse /home/muse
RUN pip install --upgrade pip
RUN pip install Flask
RUN pip install protobuf 
RUN pip install ply

ADD ./pysmt /home/muse/pysmt
RUN yes | python /home/muse/pysmt/install.py --z3
#RUN pip install pysmt
#RUN yes | pysmt-install --z3
#RUN pysmt-install --env

# Copy the current directory contents into the container at /home/muse
ADD ./verivita /home/muse/verivita
ADD ./run.sh /home/muse/run.sh
ADD ./runweb.sh /home/muse/runweb.sh
ADD ./runworker.sh /home/muse/runworker.sh

# Define environment variable
ENV NAME World
ENV PYTHONPATH "/home/muse/verivita/cbverifier:/home/muse/verivita/software:/home/muse/verivita:/home/muse/pysmt:/root/.smt_solvers/python-bindings-2.7"
ENV LD_LIBRARY_PATH "/root/.smt_solvers/python-bindings-2.7"
ENV NUXMV_PATH "/home/muse/verivita/software/nuXmv-1.1.1-Linux/bin/nuXmv"
ENV VERIVITA_PATH "/home/muse/verivita"
ENV PATH="/home/muse/verivita/software/nuXmv-1.1.1-Linux/bin:${PATH}"
ENV MEM_LIMIT 5000000
ENV TIME_LIMIT 600
#ENV PATH "/root/.smt_solvers/python-bindings-2.7":${PATH}
#ENV Z3_LIBRARY_PATH "/root/.smt_solvers/python-bindings-2.7/libz3.so"
#ENV THISISWHEREZSOIS "/root/.smt_solvers/python-bindings-2.7/libz3.so"


EXPOSE 5000

# Run app.py when the container launches
CMD ["/home/muse/run.sh"]
#CMD ["python", "/app/cbverifier/driver.py"]
