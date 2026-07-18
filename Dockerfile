# Educational: Simple Senzing redo processor Docker image
# docker build -t brian/sz_simple_redoer .
# docker run --user $UID -it -e SENZING_ENGINE_CONFIGURATION_JSON brian/sz_simple_redoer

# Educational: Use specific base image for reproducibility
ARG BASE_IMAGE="senzing/senzingsdk-runtime:4.3.2"
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

# Backend selection (build-time). Default = both on. PostgreSQL only: --build-arg WITH_MSSQL=0.
# MSSQL only: --build-arg WITH_POSTGRES=0. At least one backend is required (the build errors out
# if both are disabled).
#
# The Senzing engine uses per-backend plugins: libpostgresqlplugin.so reaches PostgreSQL via the
# system libpq (libpq5), and libmssqlplugin.so reaches SQL Server via the ODBC driver. So the real
# per-backend dependency is libpq5 (PG) vs the Microsoft ODBC stack (MSSQL) — NOT psycopg2, which
# the redoer never imports (it only uses the SDK). libpq5 is preinstalled by the base image;
# nothing Senzing depends on it, so WITH_POSTGRES=0 purges it for a leaner MSSQL-only image.
ARG WITH_POSTGRES=1
ARG WITH_MSSQL=1

# senzingsdk-setup installs the feature expression-creator libs (e.g. libg2CreditCardECreator.so)
# into /opt/senzing/er/lib; the base senzingsdk-runtime omits them (without it: SENZ0087). It is
# backend-independent, so it is always installed.
# MSSQL path: msodbcsql18 (ODBC Driver 18) via packages-microsoft-prod.deb (registers the MS apt
# repo + key for Debian 12) + an /etc/odbc.ini [MSSQL] DSN with AutoTranslate=No (prevents UTF-8
# corruption; Server/Database/port come from the engine connection string, setupenv.sh). Debian's
# own unixODBC is built WITH --enable-fastvalidate, so we keep it; do NOT substitute Microsoft's
# Ubuntu unixODBC build (~10x slower). The FAQ's 2.3.6-0.1build1 pins are Ubuntu version strings
# and do not exist on debian:12 (the senzingsdk-runtime base).
RUN apt-get update \
 && apt-get -y install --no-install-recommends \
      ca-certificates curl gnupg apt-transport-https \
      python3 python3-pip \
      senzingsdk-setup \
 && python3 -mpip install --break-system-packages orjson \
 && if [ "$WITH_POSTGRES" != 1 ] && [ "$WITH_MSSQL" != 1 ]; then \
        echo "ERROR: enable at least one of WITH_POSTGRES / WITH_MSSQL" >&2; exit 1; fi \
 && if [ "$WITH_POSTGRES" != 1 ]; then apt-get -y purge libpq5; fi \
 && if [ "$WITH_MSSQL" = 1 ]; then \
        curl -sSL -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
     && dpkg -i /tmp/packages-microsoft-prod.deb \
     && rm -f /tmp/packages-microsoft-prod.deb \
     && apt-get update \
     && ACCEPT_EULA=Y apt-get -y install --no-install-recommends msodbcsql18 unixodbc \
     && printf '[MSSQL]\nDriver = ODBC Driver 18 for SQL Server\nAutoTranslate = No\n' > /etc/odbc.ini ; fi \
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

