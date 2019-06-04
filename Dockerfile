FROM python:3.7

# will open port 80 for the webserver to be run on
EXPOSE 80
ENTRYPOINT ["/init"]

# Establish user ID of container while running
RUN groupadd -g 20000 domainusers \
    && useradd -u 20007 -g 20000 -c "Microlensing user" -d /home/robouser -s /bin/bash robouser

RUN apt-get -y update \
	&& apt-get -y install gfortran \
	&& apt-get -y clean

WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install numpy gunicorn==19.9.0 \
	&& pip --no-cache-dir install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --no-input
CMD [ "gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--access-logfile=-", "--error-logfile=-", "ZTF_TOM.wsgi:application" ]

