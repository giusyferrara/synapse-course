FROM python:3.12-slim
LABEL description="ShopSecure - Deliberately Vulnerable E-Commerce App"
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping net-tools curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask==3.0.0
WORKDIR /app
COPY app.py /app/
COPY cookie_check.html /app/
COPY mitigations.html /app/
COPY mitigation_challenges.html /app/
COPY csrf_challenge.html /app/
COPY chat_widget.html /app/
COPY synapse_a11y.css /app/
COPY synapse_a11y.js /app/
COPY synapse_a11y_toolbar.css /app/
COPY synapse_a11y_toolbar.js /app/
COPY synapse_focus.js /app/
RUN mkdir -p /app/data/invoices
EXPOSE 8080
CMD ["python3", "app.py"]
