# Build with:
# docker build --rm -t optimizer-test ./
# Run with:
# docker run --rm -p 8008:8000 -v $PWD:/opt/Optimizer -ti optimizer-test:latest
FROM python:3.6-slim-buster
COPY requirements.txt ./
RUN sed -i -e '/mysqlclient/d' requirements.txt
RUN pip install -r requirements.txt
ENV OPTIMIZER_READ_CONFIG_FILE True
ENV SECRET_KEY "some secret sring"
ENV APP_HOST localhost
ENV OPTIMIZER_DNS localhost
WORKDIR /opt/Optimizer
CMD ./manage.py migrate && ./manage.py runserver 0.0.0.0:8000
