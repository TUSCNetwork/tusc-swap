FROM python:3.7.3
ADD . /app
WORKDIR /app
RUN pip install bottle requests pyyaml gunicorn
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "main:app"]