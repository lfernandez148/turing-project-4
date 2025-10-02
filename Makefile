.PHONY: up down ps logs clean

# Docker compose file
COMPOSE_FILE=docker/docker-compose.yml

# Docker compose commands
up:
	docker compose -f $(COMPOSE_FILE) up -d

down:
	docker compose -f $(COMPOSE_FILE) down

ps:
	docker compose -f $(COMPOSE_FILE) ps

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

clean:
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
