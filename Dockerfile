# Simple dockerfile template (not yet working)

FROM python:3.11
WORKDIR /app
COPY . /app
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
RUN mkdir -p data/db logs
EXPOSE 8000
CMD ["/bin/bash", "-c", "source venv/bin/activate && hypercorn your_script_name:app -b 0.0.0.0:8000"]
