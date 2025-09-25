FROM ubuntu/squid:latest

# Install Squid
RUN apt-get update && apt-get install -y \
    squid \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /etc/squid

# Copy Squid config
COPY squid.conf .

# Expose port (internal only)
EXPOSE 3128

# Run Squid
CMD ["squid", "-N"]