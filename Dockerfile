ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip

# Python 3 HTTP Server serves the current working dir
WORKDIR /data

# Copy data for add-on
COPY run_simple.sh /
RUN chmod a+x /run_simple.sh

CMD [ "/run_simple.sh" ]