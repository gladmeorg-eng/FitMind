#!/bin/bash
# FILE: nginx/renew-certs.sh
# Auto-renew Let's Encrypt certificates

 certbot renew --webroot -w /var/www/certbot --quiet

# Reload nginx to pick up new certs
nginx -s reload

# Log renewal
logger "FitMind SSL certificates renewed"
