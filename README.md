# WatchAlong Server

Server implementation for [WatchAlong](https://github.com/shibijm/watchalong)

[![Latest Release](https://img.shields.io/github/v/release/shibijm/watchalong-server?label=Latest%20Release)](https://github.com/shibijm/watchalong-server/releases/latest)
[![Build Status](https://img.shields.io/github/actions/workflow/status/shibijm/watchalong-server/release.yml?label=Build&logo=github)](https://github.com/shibijm/watchalong-server/actions/workflows/release.yml)

## Client

https://github.com/shibijm/watchalong

## Download

Downloadable builds are available on the [releases page](https://github.com/shibijm/watchalong-server/releases).

## Docker

### Image

[ghcr.io/shibijm/watchalong-server](https://ghcr.io/shibijm/watchalong-server)

### Docker Compose example

```yaml
services:
  watchalong-server:
    container_name: watchalong-server
    image: ghcr.io/shibijm/watchalong-server:latest
    restart: unless-stopped
  ports:
    - 127.0.0.1:22334:22334
```

## Configuration - Environment Variables

- `BIND_ADDRESS` (default: `0.0.0.0`)
- `BIND_PORT` (default: `22334`)
