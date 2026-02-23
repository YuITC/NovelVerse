from pydantic import BaseModel


class NominationStatus(BaseModel):
    """Response for GET/POST /novels/{id}/nominate."""
    is_nominated: bool           # did current user nominate this novel today?
    nominations_remaining: int   # how many daily votes the user has left


class LeaderboardEntry(BaseModel):
    rank: int
    novel_id: str
    score: int
    novel: dict | None = None    # populated with NovelListItem-like fields


class LeaderboardResponse(BaseModel):
    period: str
    entries: list[LeaderboardEntry]
