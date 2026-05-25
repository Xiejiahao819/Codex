# 金融信息-产业链映射系统 MVP 落地稿（V1）

> 目标：把新闻/政策/公司事件自动转化为“行业与个股影响信号”，并结合历史数据识别主题兴衰周期。

## 1. PostgreSQL 建表 SQL（可直接执行）

```sql
-- 建议：PostgreSQL 15+
-- 可选：CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS news_raw (
  id BIGSERIAL PRIMARY KEY,
  source VARCHAR(128) NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  published_at TIMESTAMPTZ NOT NULL,
  language VARCHAR(16) DEFAULT 'zh',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_structured (
  id BIGSERIAL PRIMARY KEY,
  news_id BIGINT REFERENCES news_raw(id) ON DELETE CASCADE,
  event_type VARCHAR(64) NOT NULL,
  summary TEXT NOT NULL,
  entities_json JSONB NOT NULL,
  sentiment SMALLINT NOT NULL CHECK (sentiment IN (-1, 0, 1)),
  impact_scope VARCHAR(32) NOT NULL,
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  event_time TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS industry (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  parent_id BIGINT REFERENCES industry(id),
  market VARCHAR(16) NOT NULL,
  aliases_json JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS company (
  id BIGSERIAL PRIMARY KEY,
  ticker VARCHAR(32) NOT NULL,
  name VARCHAR(128) NOT NULL,
  market VARCHAR(16) NOT NULL,
  industry_id BIGINT REFERENCES industry(id),
  aliases_json JSONB DEFAULT '[]'::jsonb,
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE (ticker, market)
);

CREATE TABLE IF NOT EXISTS company_industry_relation (
  id BIGSERIAL PRIMARY KEY,
  company_id BIGINT NOT NULL REFERENCES company(id) ON DELETE CASCADE,
  industry_id BIGINT NOT NULL REFERENCES industry(id) ON DELETE CASCADE,
  relation_type VARCHAR(32) NOT NULL,
  weight NUMERIC(5,4) NOT NULL CHECK (weight >= 0 AND weight <= 1),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (company_id, industry_id, relation_type)
);

CREATE TABLE IF NOT EXISTS event_industry_impact (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES event_structured(id) ON DELETE CASCADE,
  industry_id BIGINT NOT NULL REFERENCES industry(id) ON DELETE CASCADE,
  direction SMALLINT NOT NULL CHECK (direction IN (-1, 1)),
  strength NUMERIC(6,2) NOT NULL CHECK (strength >= 0 AND strength <= 100),
  lag_days INTEGER DEFAULT 0,
  duration_days INTEGER DEFAULT 0,
  reasoning TEXT,
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE IF NOT EXISTS event_company_impact (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT NOT NULL REFERENCES event_structured(id) ON DELETE CASCADE,
  company_id BIGINT NOT NULL REFERENCES company(id) ON DELETE CASCADE,
  direction SMALLINT NOT NULL CHECK (direction IN (-1, 1)),
  strength NUMERIC(6,2) NOT NULL CHECK (strength >= 0 AND strength <= 100),
  reasoning TEXT,
  confidence NUMERIC(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE IF NOT EXISTS theme (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(128) UNIQUE NOT NULL,
  keywords_json JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS theme_daily_signal (
  id BIGSERIAL PRIMARY KEY,
  theme_id BIGINT NOT NULL REFERENCES theme(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  news_heat NUMERIC(8,2) DEFAULT 0,
  policy_heat NUMERIC(8,2) DEFAULT 0,
  market_heat NUMERIC(8,2) DEFAULT 0,
  composite_score NUMERIC(8,2) DEFAULT 0,
  stage VARCHAR(16) NOT NULL,
  UNIQUE (theme_id, date)
);

CREATE TABLE IF NOT EXISTS price_daily (
  id BIGSERIAL PRIMARY KEY,
  ticker VARCHAR(32) NOT NULL,
  market VARCHAR(16) NOT NULL,
  date DATE NOT NULL,
  open NUMERIC(18,6) NOT NULL,
  high NUMERIC(18,6) NOT NULL,
  low NUMERIC(18,6) NOT NULL,
  close NUMERIC(18,6) NOT NULL,
  volume NUMERIC(20,2) DEFAULT 0,
  turnover NUMERIC(20,2) DEFAULT 0,
  UNIQUE (ticker, market, date)
);
```

## 2. FastAPI 项目目录模板

```text
mvp-finance-signal/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  └─ db.py
│  ├─ models/
│  │  ├─ news.py
│  │  ├─ event.py
│  │  ├─ industry.py
│  │  ├─ company.py
│  │  └─ impact.py
│  ├─ schemas/
│  │  ├─ event.py
│  │  ├─ industry.py
│  │  └─ company.py
│  ├─ services/
│  │  ├─ ingest_service.py
│  │  ├─ impact_service.py
│  │  └─ theme_service.py
│  └─ api/
│     ├─ events.py
│     ├─ industries.py
│     ├─ companies.py
│     └─ themes.py
├─ tests/
│  ├─ test_events_api.py
│  └─ test_impact_engine.py
├─ requirements.txt
└─ README.md
```

## 3. 3 个关键接口示例（可跑骨架）

### 3.1 `GET /events`
- 用途：按时间与关键词查询结构化事件。
- 返回：事件 + 置信度 + 基础情感。

### 3.2 `GET /events/{id}`
- 用途：查看事件详情与行业/公司影响。
- 返回：`event + event_industry_impact + event_company_impact`。

### 3.3 `GET /companies/{ticker}/decompose`
- 用途：企业信息分解成产业/供应链影响。
- 返回：公司主行业、关联行业、近期受影响事件。

可运行最小示例：

```python
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Finance Signal MVP")

MOCK_EVENTS = [
    {"id": 1, "title": "某地出台 AI 产业政策", "sentiment": 1, "confidence": 0.87},
    {"id": 2, "title": "国际油价大幅波动", "sentiment": -1, "confidence": 0.78},
]

@app.get("/events")
def list_events(keyword: str | None = None):
    if not keyword:
        return MOCK_EVENTS
    return [e for e in MOCK_EVENTS if keyword.lower() in e["title"].lower()]

@app.get("/events/{event_id}")
def get_event(event_id: int):
    event = next((e for e in MOCK_EVENTS if e["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return {
        "event": event,
        "industry_impacts": [
            {"industry": "AI 软件", "direction": 1, "strength": 82},
            {"industry": "半导体", "direction": 1, "strength": 74},
        ],
        "company_impacts": [
            {"ticker": "000001", "direction": 1, "strength": 65},
            {"ticker": "000002", "direction": -1, "strength": 20},
        ],
    }

@app.get("/companies/{ticker}/decompose")
def decompose_company(ticker: str):
    return {
        "ticker": ticker,
        "direct_industry": "智能汽车",
        "related_industries": [
            {"industry": "动力电池", "relation": "上游", "weight": 0.82},
            {"industry": "车规芯片", "relation": "上游", "weight": 0.78},
            {"industry": "汽车玻璃", "relation": "上游", "weight": 0.64},
        ],
        "recent_events": [1, 2],
    }
```

## 4. MVP 实施顺序（8 周）

1. 第 1-2 周：数据入湖（新闻+政策）+ 事件结构化。
2. 第 3-4 周：事件→行业评分 + 事件详情页。
3. 第 5-6 周：公司分解 + 产业链关系图。
4. 第 7-8 周：主题周期识别 + 基础回测（1/5/20 日）。

## 5. 立即执行清单（今天）

- 只选一个市场（建议 A 股）。
- 只选三个主题（AI、智能汽车、跨境电商）。
- 只接两类源（新闻 + 政策）。
- 先把 `GET /events`、`GET /events/{id}`、`GET /companies/{ticker}/decompose` 跑通。

