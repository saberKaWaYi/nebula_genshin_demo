# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python backend with two components:
- **FastAPI Web API**: Neo4j database operations via RabbitMQ message queue
- **Crawler**: Genshin Impact character social network data scraper

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start Web API
python main.py web                 # default: host=0.0.0.0, port=8000
python main.py web --port 9000     # custom port
python main.py web --no-reload     # production mode (no hot reload)

# Run crawler
python main.py crawler

# Docker build (runs crawler via cron)
docker build -t neo4j-web .
docker run -d --name neo4j-web neo4j-web
```

## Environment Setup

Copy `.env.example` to `.env` and configure:
- Neo4j: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`
- RabbitMQ: `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`

## Architecture

```
main.py          → Unified entry point (argparse: web/crawler)
config.py        → All configuration: Settings (pydantic-settings) + CrawlerSettings + logging
app/             → FastAPI application
  main.py        → App creation with lifespan (manages Neo4j/RabbitMQ connections)
  services/      → neo4j_service.py, rabbitmq_service.py
  api/v1/        → Router + endpoints (producer.py, consumer.py)
crawler/         → Genshin crawler module
  genshin.py     → GenshinCrawler class
  crontab.txt    → Docker cron schedule (daily at 00:00)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/messages/send` | POST | Send message to RabbitMQ queue |
| `/api/v1/messages/consume` | GET | Consume message, execute Neo4j operation |
| `/api/v1/messages/health` | GET | Health check |

## Message Operations

Supported operations in message payload:
- `add_nodes`: Batch insert nodes `{label, nodes: [{id, properties}]}`
- `add_edges`: Batch insert edges `{label, edges: [{id, source_id, target_id, properties}]}`
- `delete_nodes`: Batch delete nodes `{node_ids, cascade: bool}`
- `delete_edges`: Batch delete edges `{edge_ids}`

## Crawler

`GenshinCrawler` scrapes wiki.biligame.com for Genshin Impact character data:
1. Fetch character names (Chinese + English)
2. Extract social network relationships from voice data
3. Output to `crawler/data/social_network.json`

Requires valid `SESSDATA` cookie in `config.py` → `CrawlerSettings.website_cookies`.