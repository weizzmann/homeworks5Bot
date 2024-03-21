# pull official base image
FROM python:3.11.3-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy project
COPY . /usr/src/app/

# install dependencies
RUN pip install --upgrade pip \ 
        && pip install --no-cache-dir -r requirements.txt

# run bot
CMD ["python", "bot.py"]



