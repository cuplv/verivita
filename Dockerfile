#Use an official Python runtime as a parent image
FROM python:2.7-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD ./cbverifier /app/cbverifier
ADD ./nuXmv-1.1.1-linux64.tar.gz /app/nuXmv-1.1.1-linux64.tar.gz
ADD ./web/verivita-web/target/universal/play-elm-example-1.0-SNAPSHOT/* /app/web/

# Install any needed packages specified in requirements.txt
#RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update
RUN pip install protobuf 
RUN pip install ply
RUN pip install pysmt
RUN yes | pysmt-install --z3
RUN pip install jep
#RUN apt-get install -y wget
#RUN apt-get install dtrx
#RUN dtrx /app/nuXmv-1.1.1-linux64.tar.gz

# Make port 80 available to the world outside this container
EXPOSE 80
EXPOSE 9000

# Define environment variable
ENV NAME World
ENV PYTHONPATH "/app"

# Run app.py when the container launches
CMD ["sleep", "9999"]
#CMD ["python", "/app/cbverifier/driver.py"]
