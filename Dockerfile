# pull official base image
FROM python:3.10-slim-bullseye

# create app user
RUN useradd -m appuser

# set work directory
WORKDIR /usr/src/app

# make directory writable for appuser
RUN mkdir -p /usr/src/app && chown -R appuser:appuser /usr/src/app

# environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# copy project files
COPY . /usr/src/app/

# install python dependencies (still as root → safer)
USER root
RUN pip install --upgrade pip && pip install -r requirements.txt

# change file owner to appuser after installation
RUN chown -R appuser:appuser /usr/src/app

RUN mkdir -p /usr/src/app/src/db \
    && chown -R appuser:appuser /usr/src/app/src/db


# switch to non-root user
USER appuser

# expose port
EXPOSE 5000

# run gunicorn as non-root user
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5000", "src.app:app"]
