# Docker Deployment Guide

This guide explains how to deploy the documentation scraper to a production environment using Docker Compose. 

**The system is configured for production by default and changes must be made for a local dev enviornment to work.**

## Prerequisites
- Docker and Docker Compose installed.
- A domain name pointed at the VPS.
- Cloudflare Authenticated Origin Pull certificates (`cert.pem` and `key.pem`).

## Production Configuration

### 1. Place Cloudflare Certificates
Place your `cert.pem` and `key.pem` files inside the `./caddy/` directory. The `docker-compose.yml` file is already configured to use them by default.

### 2. Configure Proxy (Optional)
In production, we need to use a proxy for outbound requests:
1.  Create a directory named `proxy-config`.
2.  Inside it, create a file named `proxychains4.conf`.
3.  Edit `proxy-config/proxychains4.conf` and add your proxy details under the `[ProxyList]` section.

### 3. Set Environment Variables
Create a `.env` file for your production secrets and domain:

```env
# .env (production)
# This should match the domain covered by your Cloudflare certificates.
DOMAIN_NAME=api.homekeepr.co

# Add any other required secrets
SCRAPER_SECRET=your_production_secret
```

## Deployment

### Initial Deployment
Run the services in detached mode:
```bash
docker-compose up -d
```

### Zero-Downtime Updates
For zero-downtime deployments, use the provided script:
```bash
./deploy.sh
```
The script handles pulling the latest code, building the new image, and gracefully switching traffic without downtime.

## Accessing the App
Once deployed, the application will be available at `https://api.homekeepr.co`.

## Local Development
For instructions on how to run the application on a local machine, please see the "Local Development Setup" section in the main `README.md` file.
