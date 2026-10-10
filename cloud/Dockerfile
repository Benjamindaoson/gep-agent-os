FROM python:3.12-slim
WORKDIR /app
COPY cloud/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY cloud /app/cloud
ENV PYTHONUNBUFFERED=1 GEP_ENV=production
EXPOSE 8080
CMD ["uvicorn","cloud.app:app","--host","0.0.0.0","--port","8080","--proxy-headers","--forwarded-allow-ips","*"]
