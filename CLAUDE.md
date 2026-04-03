# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python backend project that implements script-based data crawling, Neo4j data storage, and web API services

## Environment Setup

Python virtual environment: `myvenv`

Activate the virtual environment:
```bash
myvenv\Scripts\activate  # Windows
```

Install dependencies:
```bash
pip install -r requirements.txt
```

The project uses Tsinghua University's PyPI mirror for faster package installation in China.

## Running the Code

Run the main project:
```bash
python main.py
```

Run the Genshin social network scraper:
```bash
python scripts/get_Genshin_social_network.py
```

## Docker

Build and run with Docker:
```bash
sudo docker run --rm neo4j
```

## Architecture

- `main.py`: Entry point (currently minimal)
- `scripts/get_Genshin_social_network.py`: Web scraper for Genshin Impact character data
  - `GenshinSocialNetwork` class handles scraping from wiki.biligame.com
  - Currently extracts character names from the character list page
  - Designed to be extended for building social network relationships

## Key Dependencies

- `requests`: HTTP requests for web scraping
- `beautifulsoup4`: HTML parsing
