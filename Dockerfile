# Build with:
# docker build --rm -t optimizer-test ./
# Run with:
# docker run --rm -p 8008:8000 -v $PWD:/opt/Optimizer -ti optimizer-test:latest
FROM python:3.6-slim-buster
COPY req.txt ./
RUN sed -i -e '/mysqlclient/d' req.txt
RUN apt-get update
RUN apt-get -y install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 gettext #libgdk-pixbuf2.0-0
RUN pip install -r req.txt
ENV OPTIMIZER_READ_CONFIG_FILE True
ENV SECRET_KEY "some secret sring"
ENV APP_HOST localhost
ENV OPTIMIZER_DNS localhost
WORKDIR /opt/Optimizer
CMD ./manage.py migrate && ./manage.py compilemessages && ./manage.py runserver 0.0.0.0:8000
