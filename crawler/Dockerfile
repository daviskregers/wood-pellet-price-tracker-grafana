FROM python:3.7-alpine

WORKDIR //app

RUN apk update && apk add gcc python3-dev musl-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./crawl.py" ]