FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --create-home appuser
COPY --chown=appuser:appuser app ./app
RUN mkdir logs && chown appuser:appuser logs
USER appuser
EXPOSE 9394
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9394"]
