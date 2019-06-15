FROM python:3.7

ENTRYPOINT [ "/app/docker/init" ]

RUN apt-get -y update \
	&& apt-get -y install gfortran \
	&& apt-get -y clean

WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install numpy gunicorn==19.9.0 \
	&& pip --no-cache-dir install -r requirements.txt

COPY . .
