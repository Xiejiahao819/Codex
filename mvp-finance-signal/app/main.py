from fastapi import FastAPI, HTTPException, Query

from app.schemas.models import CompanyDecomposeResponse, EventDetailResponse, EventSummary

app = FastAPI(title="Finance Signal MVP", version="0.1.0")

MOCK_EVENTS = [
    EventSummary(id=1, title="某地出台 AI 产业政策", sentiment=1, confidence=0.87),
    EventSummary(id=2, title="国际油价大幅波动", sentiment=-1, confidence=0.78),
]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/events", response_model=list[EventSummary])
def list_events(keyword: str | None = Query(default=None, description="Filter by keyword")):
    if not keyword:
        return MOCK_EVENTS
    key = keyword.lower()
    return [event for event in MOCK_EVENTS if key in event.title.lower()]


@app.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int):
    event = next((e for e in MOCK_EVENTS if e.id == event_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")

    return EventDetailResponse(
        event=event,
        industry_impacts=[
            {"industry": "AI 软件", "direction": 1, "strength": 82},
            {"industry": "半导体", "direction": 1, "strength": 74},
        ],
        company_impacts=[
            {"ticker": "000001", "direction": 1, "strength": 65},
            {"ticker": "000002", "direction": -1, "strength": 20},
        ],
    )


@app.get("/companies/{ticker}/decompose", response_model=CompanyDecomposeResponse)
def decompose_company(ticker: str):
    return CompanyDecomposeResponse(
        ticker=ticker,
        direct_industry="智能汽车",
        related_industries=[
            {"industry": "动力电池", "relation": "上游", "weight": 0.82},
            {"industry": "车规芯片", "relation": "上游", "weight": 0.78},
            {"industry": "汽车玻璃", "relation": "上游", "weight": 0.64},
        ],
        recent_events=[1, 2],
    )
