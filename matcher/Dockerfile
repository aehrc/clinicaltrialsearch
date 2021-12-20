FROM tiangolo/uwsgi-nginx-flask:python3.6

LABEL maintainer="Bevan Koopman <bevan.koopman@csiro.au>"

# Install requirements
ADD requirements.txt /app
RUN pip install -r requirements.txt

# Add the app
ADD matcher-rest_service.py /app/main.py
ADD query_generation.py /app
ADD matcher.py /app
ADD patients.json /app
ADD trial_parser.py /app
ADD utils.py /app
ADD templates/* /app/templates/

