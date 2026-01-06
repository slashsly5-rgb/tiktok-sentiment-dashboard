# Project S - System Architecture Documentation

> **Project S** is a political sentiment analysis platform for monitoring and analyzing public opinion on Sarawak politics through TikTok and Facebook data collection, AI-powered analysis, and an intuitive dashboard interface for decision-makers.

## Table of Contents

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Detailed Technical Architecture](#2-detailed-technical-architecture)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Database Schema](#4-database-schema)
5. [Docker Deployment Architecture](#5-docker-deployment-architecture)
6. [Component Architecture](#6-component-architecture)
7. [Technology Stack](#7-technology-stack)

---

## 1. High-Level System Architecture

This diagram provides a stakeholder-friendly overview of the main system components and data flow.

```mermaid
graph TB
    subgraph "External Platforms"
        TikTok[TikTok Platform]
        Facebook[Facebook Platform]
    end

    subgraph "Data Collection Layer"
        Scraper[TikTok/Facebook Scraper<br/>Python + Playwright + Apify]
        N8N[n8n Workflow Automation<br/>Scheduling & Orchestration]
        Proxy[Residential Proxy Pool<br/>Anti-Bot Protection]
    end

    subgraph "Storage Layer"
        Supabase[(Supabase PostgreSQL<br/>Videos, Comments, Sentiment)]
        Files[Supabase Storage<br/>Screenshots, Media]
    end

    subgraph "Processing Layer"
        API[FastAPI Backend<br/>REST + WebSocket]
        AI[AI Analysis Engine<br/>OpenAI + Local LLM + RAG]
        Cache[Redis Cache<br/>Performance Optimization]
    end

    subgraph "Presentation Layer"
        Frontend[React Dashboard<br/>Tablet-First UI]
        Users[Ministers & ADUN<br/>Decision Makers]
    end

    TikTok -->|Scrape Data| Scraper
    Facebook -->|Scrape Data| Scraper
    Scraper -->|Via| Proxy
    Proxy -->|Clean Traffic| TikTok
    Proxy -->|Clean Traffic| Facebook
    N8N -->|Schedule & Trigger| Scraper
    Scraper -->|Store Raw Data| Supabase
    Scraper -->|Store Media| Files
    Supabase -->|Read Data| API
    API -->|Query Cache| Cache
    Cache -->|Return Data| API
    API -->|Request Analysis| AI
    AI -->|Store Results| Supabase
    API -->|Serve Data| Frontend
    Frontend -->|Real-time Updates| Users
    Users -->|View & Interact| Frontend

    style TikTok fill:#000,stroke:#69C9D0,color:#fff
    style Facebook fill:#1877F2,stroke:#1877F2,color:#fff
    style Scraper fill:#3776AB,stroke:#3776AB,color:#fff
    style N8N fill:#EA4B71,stroke:#EA4B71,color:#fff
    style Supabase fill:#3ECF8E,stroke:#3ECF8E,color:#fff
    style API fill:#009688,stroke:#009688,color:#fff
    style Frontend fill:#61DAFB,stroke:#61DAFB,color:#000
    style AI fill:#FF6F00,stroke:#FF6F00,color:#fff
```

### Key Components

- **Data Collection Layer**: Automated scraping with anti-bot protection
- **Storage Layer**: Cloud-based PostgreSQL with file storage
- **Processing Layer**: API server with AI-powered analysis
- **Presentation Layer**: Intuitive dashboard for decision-makers

---

## 2. Detailed Technical Architecture

This diagram shows the complete Docker container architecture with all services and their relationships.

```mermaid
graph TB
    subgraph "External Services"
        TT[TikTok API/Web]
        FB[Facebook API/Web]
        OpenAI[OpenAI API<br/>GPT-4]
    end

    subgraph "Docker Environment - Local GPU Server"
        subgraph "Scraping Containers"
            SC[Scraper Service<br/>Python 3.11 + Playwright<br/>Port: 8001]
            Apify[Apify SDK Integration<br/>TikTok Scraper Actor]
            ProxyPool[Proxy Manager<br/>Residential Proxies<br/>Rotation Logic]
        end

        subgraph "Orchestration"
            N8N_C[n8n Container<br/>Workflow Engine<br/>Port: 5678]
            Celery[Celery Workers<br/>Background Jobs<br/>Video Processing]
        end

        subgraph "Backend Services"
            FastAPI_C[FastAPI Container<br/>Python 3.11<br/>Port: 8000<br/>REST + WebSocket]
            LLM[Local LLM Container<br/>Llama 2 20B<br/>GPU Enabled<br/>Port: 8080]
            RAG[RAG Service<br/>LangChain + ChromaDB<br/>Sarawak Context]
        end

        subgraph "Data Layer"
            Redis_C[Redis Container<br/>Cache + Queue<br/>Port: 6379]
            Chroma[ChromaDB<br/>Vector Embeddings<br/>Port: 8081]
        end

        subgraph "Frontend"
            React_C[React App Container<br/>Vite + TypeScript<br/>Port: 3000]
        end

        subgraph "Infrastructure"
            Nginx_C[Nginx Reverse Proxy<br/>SSL + Load Balancing<br/>Port: 80/443]
        end
    end

    subgraph "External Database"
        Supabase_DB[(Supabase PostgreSQL<br/>Cloud Hosted<br/>Port: 5432)]
        Supabase_Storage[Supabase Storage<br/>Media Files]
    end

    subgraph "Users"
        Browser[Web Browser<br/>Tablet/Desktop]
    end

    %% Data Flow Connections
    TT -.->|HTTPS| ProxyPool
    FB -.->|HTTPS| ProxyPool
    ProxyPool -->|Scrape| SC
    SC -->|Use Actors| Apify
    SC -->|Store Data| Supabase_DB
    SC -->|Upload Media| Supabase_Storage
    N8N_C -->|Trigger Jobs| SC
    N8N_C -->|Schedule| Celery
    Celery -->|Process| SC

    FastAPI_C -->|Read/Write| Supabase_DB
    FastAPI_C -->|Cache| Redis_C
    FastAPI_C -->|Job Queue| Redis_C
    FastAPI_C -->|Query| LLM
    FastAPI_C -->|Request Analysis| OpenAI
    FastAPI_C -->|RAG Query| RAG
    RAG -->|Embeddings| Chroma
    RAG -->|Context| LLM

    React_C -->|API Calls| Nginx_C
    Nginx_C -->|Proxy| FastAPI_C
    Browser -->|HTTPS| Nginx_C
    FastAPI_C -.->|WebSocket| React_C

    style SC fill:#3776AB,color:#fff
    style FastAPI_C fill:#009688,color:#fff
    style React_C fill:#61DAFB,color:#000
    style Redis_C fill:#DC382D,color:#fff
    style N8N_C fill:#EA4B71,color:#fff
    style LLM fill:#7C3AED,color:#fff
    style Supabase_DB fill:#3ECF8E,color:#fff
    style Nginx_C fill:#009639,color:#fff
```

### Container Services

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| Nginx | nginx:alpine | 80, 443 | Reverse proxy & SSL termination |
| FastAPI | python:3.11-slim | 8000 | Main API server |
| Scraper | python:3.11 | 8001 | TikTok/Facebook scraping |
| LLM | pytorch/pytorch | 8080 | Local Llama 2 20B inference |
| RAG | python:3.11 | - | Context retrieval system |
| Redis | redis:7-alpine | 6379 | Cache & job queue |
| ChromaDB | chromadb/chroma | 8081 | Vector embeddings |
| n8n | n8nio/n8n | 5678 | Workflow automation |
| React | node:20-alpine | 3000 | Frontend dashboard |
| Celery | python:3.11 | - | Background workers |

---

## 3. Data Flow Diagram

This sequence diagram illustrates the complete data processing pipeline from scraping to visualization.

```mermaid
sequenceDiagram
    autonumber
    participant N8N as n8n Scheduler
    participant Scraper as TikTok Scraper
    participant Proxy as Proxy Pool
    participant TikTok as TikTok Platform
    participant DB as Supabase DB
    participant Storage as Supabase Storage
    participant Queue as Redis Queue
    participant AI as AI Service
    participant LLM as Local LLM
    participant RAG as RAG System
    participant API as FastAPI
    participant Frontend as React Dashboard
    participant User as End User

    N8N->>Scraper: Trigger scraping job (scheduled)
    Scraper->>Proxy: Get available proxy
    Proxy-->>Scraper: Return proxy address
    Scraper->>TikTok: Search videos (via proxy)
    TikTok-->>Scraper: Return video list

    loop For each video
        Scraper->>TikTok: Fetch video details + comments
        TikTok-->>Scraper: Return video data
        Scraper->>DB: Store video metadata
        Scraper->>Storage: Upload screenshot
        Scraper->>Queue: Queue for AI analysis
    end

    Queue->>AI: Process analysis job
    AI->>DB: Fetch video + comments
    DB-->>AI: Return raw data
    AI->>RAG: Query Sarawak politics context
    RAG-->>AI: Return relevant context
    AI->>LLM: Analyze sentiment with context
    LLM-->>AI: Return analysis results
    AI->>DB: Store sentiment analysis

    User->>Frontend: Open dashboard
    Frontend->>API: GET /api/sentiment/overview
    API->>DB: Query aggregated sentiment
    DB-->>API: Return sentiment data
    API->>Frontend: JSON response
    Frontend->>User: Display dashboard

    API->>Frontend: WebSocket: Real-time updates
    Frontend->>User: Live sentiment updates
```

### Data Flow Steps

1. **Scheduled Trigger**: n8n triggers scraping jobs (hourly/daily)
2. **Proxy Rotation**: Scraper gets residential proxy to avoid detection
3. **Data Collection**: Scrape videos, comments, and metadata
4. **Storage**: Raw data stored in Supabase PostgreSQL
5. **Job Queue**: Analysis jobs queued in Redis
6. **AI Processing**: Sentiment analysis with RAG-enhanced LLM
7. **User Access**: Dashboard displays real-time insights

---

## 4. Database Schema

Entity Relationship Diagram showing all database tables and their relationships.

```mermaid
erDiagram
    VIDEOS ||--o{ COMMENTS : has
    VIDEOS ||--o| SENTIMENT_ANALYSIS : analyzed_by
    VIDEOS }o--|| CONSTITUENCIES : "belongs_to"
    SCRAPING_JOBS ||--o{ VIDEOS : produces
    USERS ||--o{ SCRAPING_JOBS : initiates

    VIDEOS {
        uuid id PK
        varchar tiktok_id UK "Unique TikTok video ID"
        text url
        varchar author_username
        text description
        text thumbnail_url
        text screenshot_url
        bigint views_count
        bigint likes_count
        bigint shares_count
        bigint comments_count
        jsonb hashtags "Array of hashtags"
        uuid constituency_id FK
        timestamp scraped_at
        timestamp created_at
    }

    COMMENTS {
        uuid id PK
        uuid video_id FK
        varchar author_username
        text text
        int likes_count
        boolean is_bot_suspected
        varchar language_detected "en/ms/dialect"
        float bot_score "0-1 probability"
        timestamp created_at
    }

    SENTIMENT_ANALYSIS {
        uuid id PK
        uuid video_id FK
        varchar overall_sentiment "positive/negative/neutral/mixed"
        decimal sentiment_score "1-10"
        varchar topic
        jsonb key_issues "Array of identified issues"
        jsonb discussion_points
        text suggested_response
        text counter_narrative
        boolean fake_news_detected
        float confidence_score
        timestamp analyzed_at
    }

    CONSTITUENCIES {
        uuid id PK
        varchar name "e.g., Kuching, Serian"
        varchar code UK "e.g., N01, N02"
        jsonb geojson_boundary "Geographic boundary"
        varchar current_sentiment
        varchar trend "improving/declining/stable"
        jsonb key_issues
        int total_videos
        int total_comments
        timestamp updated_at
    }

    SCRAPING_JOBS {
        uuid id PK
        uuid user_id FK
        varchar job_type "scheduled/manual"
        varchar status "pending/running/completed/failed"
        jsonb search_params "Keywords, filters"
        int videos_scraped
        int comments_scraped
        int videos_analyzed
        timestamp started_at
        timestamp completed_at
        text error_message
    }

    USERS {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar full_name
        varchar role "admin/analyst/viewer"
        uuid default_constituency_id FK
        boolean is_active
        timestamp last_login
        timestamp created_at
    }
```

### Key Database Features

- **UUIDs**: Primary keys for distributed system compatibility
- **JSONB**: Flexible storage for hashtags, issues, and metadata
- **Indexing**: Optimized for constituency-based queries
- **Timestamps**: Audit trail for all data changes
- **Foreign Keys**: Referential integrity maintained

---

## 5. Docker Deployment Architecture

Comprehensive deployment diagram showing local GPU server infrastructure.

```mermaid
graph TB
    subgraph "Local GPU Server - Physical Hardware"
        subgraph "Docker Host"
            subgraph "Application Stack"
                direction TB
                Nginx[Nginx Container<br/>nginx:alpine<br/>Ports: 80,443<br/>SSL Termination]

                subgraph "Backend Services"
                    FastAPI[FastAPI Container<br/>python:3.11-slim<br/>Port: 8000<br/>App Server]
                    Scraper[Scraper Container<br/>python:3.11<br/>Port: 8001<br/>Playwright + Chromium]
                    Celery_W[Celery Worker<br/>python:3.11<br/>Background Jobs]
                end

                subgraph "AI/ML Services - GPU"
                    LLM_GPU[LLM Container<br/>pytorch/pytorch<br/>Port: 8080<br/>Llama 2 20B<br/>NVIDIA Runtime]
                    RAG_Service[RAG Service<br/>python:3.11<br/>LangChain + Embeddings]
                end

                subgraph "Data Services"
                    Redis[Redis Container<br/>redis:7-alpine<br/>Port: 6379<br/>Cache + Queue]
                    ChromaDB[ChromaDB Container<br/>chromadb/chroma<br/>Port: 8081<br/>Vector Store]
                end

                subgraph "Automation"
                    N8N[n8n Container<br/>n8nio/n8n<br/>Port: 5678<br/>Workflow Engine]
                end

                Frontend[React Container<br/>node:20-alpine<br/>Port: 3000<br/>Static Build]
            end

            subgraph "Persistent Volumes"
                Vol_Redis[(Redis Data<br/>./data/redis)]
                Vol_Chroma[(ChromaDB Data<br/>./data/chromadb)]
                Vol_N8N[(n8n Data<br/>./data/n8n)]
                Vol_Models[(LLM Models<br/>./models)]
                Vol_Logs[(Application Logs<br/>./logs)]
            end
        end

        subgraph "GPU Hardware"
            GPU[NVIDIA GPU<br/>CUDA 12.x<br/>VRAM: 40GB+<br/>For Llama 2 20B]
        end
    end

    subgraph "External Cloud Services"
        Supabase_Cloud[(Supabase<br/>PostgreSQL<br/>Cloud Database)]
        Supabase_Stor[Supabase Storage<br/>Media Files]
        OpenAI_Cloud[OpenAI API<br/>GPT-4 Fallback]
    end

    subgraph "Client Devices"
        Tablet[Tablets<br/>Ministers/ADUN]
        Desktop[Desktop Browsers<br/>Analysts]
    end

    %% Network Connections
    Tablet -->|HTTPS| Nginx
    Desktop -->|HTTPS| Nginx
    Nginx -->|Proxy| FastAPI
    Nginx -->|Static Files| Frontend

    FastAPI -->|Cache| Redis
    FastAPI -->|Vector Search| ChromaDB
    FastAPI -->|LLM Inference| LLM_GPU
    FastAPI -->|RAG| RAG_Service
    FastAPI -->|DB Queries| Supabase_Cloud
    FastAPI -->|File Upload| Supabase_Stor
    FastAPI -.->|Fallback| OpenAI_Cloud

    Scraper -->|Store Data| Supabase_Cloud
    Scraper -->|Upload Media| Supabase_Stor

    N8N -->|Trigger| Scraper
    N8N -->|Schedule| Celery_W
    Celery_W -->|Execute| Scraper

    RAG_Service -->|Embeddings| ChromaDB
    RAG_Service -->|Query| LLM_GPU

    LLM_GPU -.->|Use| GPU

    Redis ---|Persist| Vol_Redis
    ChromaDB ---|Persist| Vol_Chroma
    N8N ---|Persist| Vol_N8N
    LLM_GPU ---|Load Models| Vol_Models
    FastAPI ---|Write Logs| Vol_Logs

    style GPU fill:#76B900,color:#fff
    style LLM_GPU fill:#7C3AED,color:#fff
    style Supabase_Cloud fill:#3ECF8E,color:#fff
    style Nginx fill:#009639,color:#fff
    style FastAPI fill:#009688,color:#fff
    style Frontend fill:#61DAFB,color:#000
    style Redis fill:#DC382D,color:#fff
```

### Infrastructure Requirements

**Hardware**:
- NVIDIA GPU with 40GB+ VRAM (for Llama 2 20B)
- CUDA 12.x support
- Sufficient CPU/RAM for Docker containers

**Software**:
- Docker Engine with NVIDIA Container Runtime
- Docker Compose for multi-service orchestration
- SSL certificates for HTTPS

**Persistent Storage**:
- Redis data volume
- ChromaDB embeddings
- n8n workflow configurations
- LLM model weights
- Application logs

---

## 6. Component Architecture

Detailed breakdown of the technical stack and component interactions.

```mermaid
graph LR
    subgraph "Frontend - React + TypeScript"
        UI[UI Components<br/>Tailwind CSS]
        State[State Management<br/>Zustand + React Query]
        Charts[Data Visualization<br/>Recharts]
        Maps[Geographic Maps<br/>Leaflet]
        WS_Client[WebSocket Client<br/>Real-time Updates]
    end

    subgraph "API Layer - FastAPI"
        Routes[API Routes<br/>REST Endpoints]
        WS_Server[WebSocket Server<br/>Real-time Push]
        Auth[Authentication<br/>JWT + OAuth2]
        Middleware[Middleware<br/>CORS, Logging, Rate Limit]
    end

    subgraph "Business Logic - Services"
        Scraper_Svc[Scraper Service<br/>Orchestration]
        AI_Svc[AI Service<br/>Analysis Pipeline]
        Cache_Svc[Cache Service<br/>Redis Operations]
        RAG_Svc[RAG Service<br/>Context Retrieval]
        Bot_Svc[Bot Detection<br/>ML Classifier]
    end

    subgraph "Data Access - ORM"
        Models[SQLAlchemy Models<br/>Database Schema]
        Schemas[Pydantic Schemas<br/>Validation]
        Migrations[Alembic<br/>DB Migrations]
    end

    subgraph "External Integrations"
        Playwright_Int[Playwright<br/>Browser Automation]
        Apify_Int[Apify SDK<br/>TikTok Actors]
        OpenAI_Int[OpenAI Client<br/>GPT-4 API]
        LLM_Int[LLM Client<br/>Llama 2 Local]
        Supabase_Int[Supabase Client<br/>Python SDK]
    end

    UI --> State
    State --> Routes
    Charts --> State
    Maps --> State
    WS_Client <-->|WebSocket| WS_Server

    Routes --> Auth
    Routes --> Middleware
    Routes --> Scraper_Svc
    Routes --> AI_Svc

    Scraper_Svc --> Cache_Svc
    Scraper_Svc --> Playwright_Int
    Scraper_Svc --> Apify_Int
    Scraper_Svc --> Models

    AI_Svc --> RAG_Svc
    AI_Svc --> Bot_Svc
    AI_Svc --> OpenAI_Int
    AI_Svc --> LLM_Int

    Models --> Supabase_Int
    Schemas --> Models
    Migrations --> Models

    style UI fill:#61DAFB,color:#000
    style Routes fill:#009688,color:#fff
    style Scraper_Svc fill:#3776AB,color:#fff
    style AI_Svc fill:#FF6F00,color:#fff
    style Models fill:#3ECF8E,color:#fff
```

---

## 7. Technology Stack

### Frontend Layer
- **Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand + React Query
- **Data Visualization**: Recharts
- **Maps**: Leaflet with React-Leaflet
- **Real-time**: WebSocket client
- **Build Tool**: Vite

### Backend Layer
- **API Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Authentication**: JWT with FastAPI-Users
- **WebSocket**: FastAPI native WebSocket support
- **API Docs**: Auto-generated Swagger/OpenAPI

### Data Processing Layer
- **Scraping**: Playwright + Apify SDK
- **Orchestration**: n8n (workflow automation)
- **Caching**: Redis 7.x
- **Queue**: Celery with Redis backend
- **Proxy Management**: Custom proxy pool with rotation

### AI/ML Layer
- **Sentiment Analysis**: OpenAI GPT-4
- **Reasoning Model**: Llama 2 20B (local deployment)
- **RAG System**: LangChain + ChromaDB vector store
- **Language Support**: Custom dialect dictionary + translation layer
- **Bot Detection**: ML classifier (scikit-learn)

### Storage Layer
- **Primary Database**: Supabase PostgreSQL
- **Vector Database**: ChromaDB (for RAG embeddings)
- **File Storage**: Supabase Storage (images, videos, screenshots)
- **Cache**: Redis (query cache, session storage)

### Infrastructure Layer
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **GPU Runtime**: NVIDIA Docker runtime
- **Monitoring**: Prometheus + Grafana (optional)
- **Logs**: Structured logging with rotation

---

## Design Principles

Based on the Project S UI/UX requirements:

### 1. Single-Screen Comprehension
- Core insights visible upon launch
- No navigation required for situational awareness

### 2. Plain-Language Hierarchy
- Readable summaries over dense visualizations
- Clear, concise messaging

### 3. Minimal Interaction
- Reduce reliance on filters and hidden controls
- Proactive information display

### 4. Neutral Visual Tone
- Calm, dependable presentation
- Avoid urgency or alarm cues

### 5. Tablet-First Layout
- 16:9 optimized layout
- Touch-friendly interface
- Accessible to users 60+ years old

---

## Performance Targets

- **Scraping Capacity**: 10,000 videos per day
- **Real-time Updates**: WebSocket latency < 100ms
- **API Response**: < 200ms for cached queries
- **Dashboard Load**: < 2 seconds initial load
- **Sentiment Analysis**: < 30 seconds per video

---

## Security Considerations

1. **Authentication**: JWT-based with role-based access control
2. **Data Encryption**: SSL/TLS for all external connections
3. **API Security**: Rate limiting and CORS protection
4. **Proxy Protection**: Residential proxies to avoid platform bans
5. **Secrets Management**: Environment variables, no hardcoded credentials

---

## Future Enhancements

- Cloud failover deployment for power outage scenarios
- Multi-platform expansion (Instagram, YouTube)
- Advanced bot detection with neural networks
- Automated counter-narrative generation
- Mobile app for on-the-go access

---

**Last Updated**: December 2025
**Version**: 1.0
**Contact**: Project S Development Team
