#Use an official Python runtime as a parent image
FROM python:2.7-slim

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
#RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update
RUN pip install Flask
RUN pip install protobuf 
RUN pip install ply
RUN pip install pysmt
RUN yes | pysmt-install --z3
#RUN apt-get install -y wget
#RUN apt-get install dtrx
#RUN dtrx /app/nuXmv-1.1.1-linux64.tar.gz

# Copy the current directory contents into the container at /app
ADD ./verivita /app/verivita

# Define environment variable
ENV NAME World
ENV PYTHONPATH "/app/verivita/cbverifier:/app/verivita/software:/app/verivita"
ENV NUXMV_PATH "/app/verivita/software/nuXmv-1.1.1-linux64/"
ENV VERIVITA_PATH "/app/verivita"

# Run app.py when the container launches
CMD ["python", "/app/verivita/app/app.py"]
#CMD ["python", "/app/cbverifier/driver.py"]
