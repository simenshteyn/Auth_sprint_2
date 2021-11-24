FROM python:3.9
RUN python -m pip install --upgrade pip
WORKDIR /opt/async_api
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
