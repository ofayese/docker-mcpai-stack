# Nginx Reverse Proxy for Docker MCP Stack
FROM nginx:1.29-alpine

# Install basic tools and set up directories
RUN apk add --no-cache curl && \
    mkdir -p /etc/nginx/conf.d && \
    mkdir -p /var/cache/nginx/client_temp && \
    mkdir -p /var/cache/nginx/proxy_temp && \
    mkdir -p /var/cache/nginx/fastcgi_temp && \
    mkdir -p /var/cache/nginx/uwsgi_temp && \
    mkdir -p /var/cache/nginx/scgi_temp

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx.windows.conf /etc/nginx/nginx.windows.conf

# Set proper permissions
RUN chown -R nginx:nginx /etc/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx

# Expose ports
EXPOSE 80 443 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run as nginx user for security
USER nginx

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
