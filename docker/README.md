# Docker Development

The project uses Docker for running services like ChromaDB. Docker files are organized in the `/docker` directory:

```
docker/
├── docker-compose.yml    # Main compose file
├── config/              # Configuration files
└── volumes/             # Volume mappings
```

## 🐳 Docker Commands

You can use the following make commands to manage Docker services:

```bash
make up      # Start all services
make down    # Stop all services
make ps      # Show running services
make logs    # View logs
make clean   # Clean up all containers and volumes
```

Or use docker-compose directly:

```bash
docker compose -f docker/docker-compose.yml up -d
```
