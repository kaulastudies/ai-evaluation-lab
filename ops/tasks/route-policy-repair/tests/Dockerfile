FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bubblewrap libseccomp2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY candidate_proxy.py candidate_worker.py security.py /tests/
COPY test_router.py /tests/test_router.py
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh
