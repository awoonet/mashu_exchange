FROM python:slim-buster
WORKDIR /app/
COPY ./requirements.txt ./
RUN apt install gcc
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
COPY . .
CMD ["python3", "app.py"]
