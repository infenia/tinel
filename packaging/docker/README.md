# Tinel Docker Distribution

This directory contains Docker configurations for running Tinel in containerized environments.

## 🐳 Available Images

### 1. Ubuntu-based (Full-featured)
- **File**: `Dockerfile.ubuntu`
- **Use case**: Complete system analysis with all tools
- **Size**: ~200MB
- **Features**: All system utilities, hardware detection tools

```bash
docker build -f packaging/docker/Dockerfile.ubuntu -t tinel:ubuntu .
```

### 2. Alpine-based (Lightweight)
- **File**: `Dockerfile.alpine`
- **Use case**: Resource-constrained environments
- **Size**: ~80MB  
- **Features**: Essential tools, smaller footprint

```bash
docker build -f packaging/docker/Dockerfile.alpine -t tinel:alpine .
```

### 3. Distroless (Security-focused)
- **File**: `Dockerfile.distroless`
- **Use case**: Maximum security, API-only deployments
- **Size**: ~50MB
- **Features**: Minimal attack surface, no shell access

```bash
docker build -f packaging/docker/Dockerfile.distroless -t tinel:distroless .
```

## 🚀 Quick Start

### Single Container
```bash
# Run Ubuntu variant with host system access
docker run -d \
  --name tinel \
  -p 8080:8080 \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /dev:/host/dev:ro \
  -e TINEL_HOST_PREFIX=/host \
  tinel:ubuntu
```

### Docker Compose (Recommended)
```bash
# Full-featured deployment
docker-compose up -d

# Alpine variant
docker-compose --profile alpine up -d

# Distroless variant  
docker-compose --profile distroless up -d

# With monitoring
docker-compose --profile monitoring up -d

# With Redis caching
docker-compose --profile with-cache up -d
```

## 📊 Container Variants

| Variant | Base Image | Size | Use Case | Security |
|---------|------------|------|----------|----------|
| Ubuntu | ubuntu:22.04 | ~200MB | Full system analysis | Standard |
| Alpine | alpine:3.18 | ~80MB | Lightweight deployments | Good |
| Distroless | gcr.io/distroless/python3 | ~50MB | API-only, max security | Excellent |

## 🔧 Configuration

### Environment Variables
- `TINEL_CONFIG`: Path to configuration file
- `TINEL_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `TINEL_HOST_PREFIX`: Prefix for host system paths (default: `/host`)

### Volume Mounts
```bash
# Host system access (read-only)
-v /proc:/host/proc:ro
-v /sys:/host/sys:ro  
-v /dev:/host/dev:ro

# Configuration
-v ./config:/etc/tinel:ro

# Data persistence
-v tinel-data:/var/lib/tinel
-v tinel-logs:/var/log/tinel
```

### Port Mapping
- `8080`: Main API server
- `9090`: Prometheus metrics (if enabled)

## 🛡️ Security Features

### Container Hardening
- Non-root user execution
- Read-only filesystem (where possible)
- Minimal capabilities (`CAP_DAC_OVERRIDE` only)
- No new privileges
- Temporary filesystem for `/tmp`

### Network Security
- Custom bridge network
- Port isolation
- No privileged access

### System Access
```bash
# Secure host system access
--cap-drop=ALL \
--cap-add=DAC_OVERRIDE \
--security-opt=no-new-privileges:true \
--read-only
```

## 📈 Monitoring Integration

### Prometheus Metrics
```bash
# Access metrics endpoint
curl http://localhost:8080/metrics
```

### Health Checks
```bash
# Container health status
docker ps --filter "name=tinel" --format "table {{.Names}}\t{{.Status}}"

# Manual health check
curl http://localhost:8080/health
```

### Logging
```bash
# View container logs
docker logs tinel

# Follow logs in real-time
docker logs -f tinel

# Structured JSON logging
docker logs tinel | jq .
```

## 🔄 Deployment Patterns

### Development
```bash
# Quick development setup
docker run --rm -it \
  -p 8080:8080 \
  -v $(pwd):/app \
  -v /proc:/host/proc:ro \
  tinel:ubuntu python3 -m tinel server --debug
```

### Production
```yaml
# Docker Compose production example
version: '3.8'
services:
  tinel:
    image: tinel:ubuntu
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - ./config:/etc/tinel:ro
      - tinel-data:/var/lib/tinel
    environment:
      - TINEL_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tinel
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tinel
  template:
    metadata:
      labels:
        app: tinel
    spec:
      containers:
      - name: tinel
        image: tinel:ubuntu
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: host-proc
          mountPath: /host/proc
          readOnly: true
        - name: host-sys
          mountPath: /host/sys
          readOnly: true
        env:
        - name: TINEL_HOST_PREFIX
          value: "/host"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
      volumes:
      - name: host-proc
        hostPath:
          path: /proc
      - name: host-sys
        hostPath:
          path: /sys
```

## 🛠️ Troubleshooting

### Common Issues
1. **Permission Denied**: Ensure proper volume mounts and capabilities
2. **Host Access Failed**: Check `/host` prefix configuration
3. **Container Won't Start**: Verify resource limits and dependencies

### Debug Commands
```bash
# Interactive shell (Ubuntu/Alpine only)
docker exec -it tinel /bin/bash

# Check system access
docker exec tinel ls -la /host/proc

# Verify configuration
docker exec tinel cat /etc/tinel/config.yaml

# Test hardware detection
docker exec tinel python3 -m tinel hardware --debug
```

### Performance Tuning
```bash
# Adjust memory limits
docker run --memory=512m tinel:ubuntu

# CPU limits
docker run --cpus=2 tinel:ubuntu

# Optimize for specific workloads
docker run -e TINEL_WORKERS=8 tinel:ubuntu
```

## 📋 Best Practices

1. **Use specific image tags** in production
2. **Enable health checks** for all deployments
3. **Mount host filesystems read-only** when possible
4. **Use secrets management** for sensitive configuration
5. **Implement proper logging** aggregation
6. **Monitor resource usage** and set appropriate limits
7. **Regular security updates** of base images

## 🔗 Registry Information

### Official Images
- Docker Hub: `docker pull tinel/tinel:latest`
- GitHub Container Registry: `docker pull ghcr.io/infenia/tinel:latest`
- Quay.io: `docker pull quay.io/infenia/tinel:latest`

### Image Tags
- `latest`: Ubuntu-based full-featured
- `alpine`: Alpine-based lightweight
- `distroless`: Security-focused minimal
- `v0.1.0`: Specific version tags
- `dev`: Development builds