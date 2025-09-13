# Educational: Simple Senzing redo processor Docker image
# docker build -t brian/sz_simple_redoer .
# docker run --user $UID -it -e SENZING_ENGINE_CONFIGURATION_JSON brian/sz_simple_redoer

# Educational: Use specific base image for reproducibility
ARG BASE_IMAGE="senzing/senzingsdk-runtime:latest"
FROM ${BASE_IMAGE}
ARG BASE_IMAGE
RUN echo "Building from base image: $BASE_IMAGE"

# Educational: Proper labeling for container management
LABEL Name="brian/sz_simple_redoer" \
      Maintainer="brianmacy@gmail.com" \
      Version="DEV" \
      Description="Simple Senzing redo processor for educational purposes" \
      Usage="docker run -e SENZING_ENGINE_CONFIGURATION_JSON=... brian/sz_simple_redoer"

USER root

# Educational: Install dependencies and clean up in single layer for efficiency
RUN apt-get update \
 && apt-get -y install --no-install-recommends curl python3 python3-pip python3-psycopg2 \
 && python3 -mpip install --break-system-packages orjson \
 && apt-get -y remove python3-pip \
 && apt-get -y autoremove \
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*

# Educational: Copy application files
COPY sz_simple_redoer.py /app/
RUN chmod +x /app/sz_simple_redoer.py

# Educational: Set Python path for Senzing SDK
ENV PYTHONPATH=/opt/senzing/er/sdk/python:/app

# Educational: Add health check for container monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Educational: Run as non-root user for security
USER 1001

WORKDIR /app
ENTRYPOINT ["/app/sz_simple_redoer.py"]

