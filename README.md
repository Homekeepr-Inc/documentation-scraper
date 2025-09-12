## Home Equipment Manuals Corpus

A comprehensive system for collecting, processing, and serving documentation for all home equipment and systems (appliances, HVAC, solar, electrical, plumbing, roofing, security) from multiple sources.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Scrapy Crawlers │───▶│  Ingestion      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
│                      │                       │
│ • Internet Archive   │ • Brand spiders       │ • PDF download
│ • ManualsLib         │ • Third-party aggs    │ • Text extraction
│ • Brand portals      │ • Parts distributors  │ • Language detect
│ • Parts sites        │ • Archive crawlers    │ • Deduplication
│                      │                       │
└──────────────────────┼───────────────────────┼─────────────────┘
                       │                       │
                       ▼                       ▼
              ┌─────────────────┐    ┌─────────────────┐
              │   Local Dev     │    │   Production    │
              └─────────────────┘    └─────────────────┘
              │                      │
              │ • SQLite + FTS5      │ • PostgreSQL
              │ • Filesystem blobs   │ • S3/R2 storage
              │ • FastAPI            │ • OpenSearch
              │ • Direct ingestion   │ • Celery workers
              │                      │ • Load balancers
              └──────────────────────┴─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   API Layer     │
              └─────────────────┘
              │
              │ • Search & filter
              │ • Full-text search
              │ • PDF downloads
              │ • Text extraction
              │ • Metadata facets
```

### Current Implementation (Local Dev)

- **Language:** Python 3.12+ with user-site packages
- **Crawling:** Scrapy framework with multiple source-specific spiders
- **Storage:** Filesystem blobs (`~/appliance-manuals/`) + SQLite with FTS5
- **API:** FastAPI with search, metadata, download, and text endpoints
- **Processing:** pdfminer.six + pypdf for text extraction, langdetect for language

## Data Sources & Coverage

### Equipment Categories

- **🏠 Appliances**: Kitchen (refrigerator, dishwasher, range, microwave), laundry (washer, dryer), water systems
- **🌡️ HVAC**: Furnaces, heat pumps, AC units, thermostats, ventilation systems
- **☀️ Solar**: Panels, microinverters, string inverters, monitoring systems, mounting hardware
- **⚡ Electrical**: Panels, outlets, switches, GFCI/AFCI, lighting controls
- **🚿 Plumbing**: Water heaters, pumps, faucets, fixtures, filtration systems
- **🏠 Roofing**: Standing seam, shingles, gutters, ventilation, flashing
- **🔒 Security**: Alarm systems, cameras, smart locks, garage door openers
- **🌿 Outdoor**: Irrigation, pool equipment, generators, outdoor lighting

### Working Sources

- **Internet Archive** (manuals collection): Primary reliable source
- **Sitemap Crawling**: Direct access to brand PDF libraries (GE working)
- **Targeted Document Crawling**: Specific doc types (installation, tech_sheet, wiring)
- **Home Equipment Spider**: HVAC, solar, electrical equipment from IA

### Brand Coverage

- **Appliances**: Whirlpool, GE, Samsung, LG, Frigidaire, Bosch (800+ docs)
- **HVAC**: Carrier, Trane, Lennox, Rheem, Goodman, York
- **Solar**: Enphase, SolarEdge, SMA, Fronius, Generac
- **Electrical**: Square D, Siemens, Eaton, Leviton, Lutron
- **Plumbing**: Kohler, Moen, Delta, American Standard

## Quickstart

**One-command setup** (Python 3.11+ required):

```bash
python3 setup.py
```

This will:

- Install all dependencies  
- Initialize the database with correct schema
- Run a sample crawl (3 documents) to verify everything works
- Show you next steps

**Then start the web UI:**

```bash
export PYTHONPATH=. && python3 -m uvicorn app.main:app --reload
```

**Browse your data:**

- 🌐 **Web UI**: <http://localhost:8000> (search, filter, download)
- 📊 **API docs**: <http://localhost:8000/docs>
- 🔍 **Search example**: `GET http://localhost:8000/documents?query=furnace&equipment_category=hvac`

## Scaling Your Corpus

```bash
# Set environment for all commands
export PYTHONPATH=.

# Large multi-brand crawl (recommended first step)
python3 scripts/simple_cli.py bulk

# Targeted document types (installation, tech_sheet, wiring, service, owner)
python3 scripts/simple_cli.py targeted whirlpool tech_sheet
python3 scripts/simple_cli.py targeted ge installation

# Brand sitemaps (bypass UI protections)
python3 scripts/simple_cli.py sitemaps

# Individual brand crawls
python3 scripts/simple_cli.py crawl-ia samsung 100

# Show corpus statistics
python3 scripts/simple_cli.py stats
```

## Data Pipeline

### 1. Discovery & Crawling

- **Scrapy spiders** for each source with custom settings (timeouts, delays, robots.txt)
- **Source-specific strategies**: JSON APIs (preferred), HTML parsing, Playwright for JS
- **Deduplication**: SHA-256 hashing prevents duplicate downloads

### 2. Ingestion & Processing

- **PDF processing**: Text extraction via pdfminer.six, metadata via pypdf
- **Language detection**: English prioritization with mixed-language support
- **Document classification**: Auto-detect owner/service/tech_sheet/install/wiring/spec
- **Storage**: Hierarchical filesystem + compressed text + SQLite metadata

### 3. Search & Retrieval

- **Full-text search**: SQLite FTS5 on extracted text
- **Metadata filtering**: Brand, model, doc_type, language, date ranges
- **API responses**: Metadata by default, full text on-demand
- **File serving**: Direct PDF downloads with proper MIME types

## Storage Schema

### Local Development

```
~/home-manuals/{equipment_category}/{brand}/{model}/{doc_type}/{sha256}.pdf
~/home-manuals/{equipment_category}/{brand}/{model}/{doc_type}/{sha256}.txt.gz
./data/manuals.db (SQLite with FTS5)
```

### Database Schema

```sql
documents (
  id, brand, model_number, doc_type, title, language, published_at,
  source_url, file_url, file_sha256, size_bytes, pages,
  ocr_applied, english_present, status, http_status,
  local_path, text_path, text, ingested_at, last_seen_at
)
```

## Production Architecture (Future)

### Storage Layer

- **Blobs**: S3/R2 with same hierarchical structure
- **Metadata**: PostgreSQL with proper indexing and constraints
- **Search**: OpenSearch/Elasticsearch with text analysis and faceting
- **Cache**: Redis for frequently accessed metadata and search results

### Processing Layer

- **Queue system**: Celery + Redis for distributed crawl → download → extract → index
- **Workers**: Horizontally scalable processing with retry logic and error handling
- **Scheduling**: Cron-based incremental crawls and corpus maintenance

### API Layer

- **Authentication**: API keys and rate limiting
- **Load balancing**: Multiple FastAPI instances behind nginx/ALB
- **Monitoring**: Per-source metrics, error rates, ingestion throughput
- **Documentation**: OpenAPI specs with interactive docs

## Current Status

- **Corpus size**: 800+ documents across 6 major appliance brands
- **Equipment coverage**: Appliances (primary), HVAC, solar, electrical (expanding)
- **Working sources**: Internet Archive (reliable), home equipment spider (working)
- **Web UI**: Full browsing interface with search and filters
- **API endpoints**: Health, search, download, text extraction, equipment filtering
- **Setup**: One-command installation with automatic verification

## Compliance & Quality

- **Robots.txt respect**: Configurable per source
- **Rate limiting**: Per-domain delays and concurrent request limits  
- **Copyright compliance**: Focus on publicly available manuals and service documents
- **Quality filtering**: English detection, PDF validation, duplicate removal
