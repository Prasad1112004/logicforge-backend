from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PlayerCreateRequest(BaseModel):
    guest_name: str | None = Field(default="Guest")


class PlayerResponse(BaseModel):
    id: int
    guest_name: str
    guest_code: str
    xp: int
    coins: int
    rank: str
    current_region_id: int | None = None
    current_mission_id: int | None = None
    performance_score: int
    completed_challenges: int = 0


class WorldRegion(BaseModel):
    id: int
    name: str
    description: str
    theme: str | None = None
    order_index: int


class MissionSummary(BaseModel):
    id: int
    region_id: int
    title: str
    description: str
    mission_type: str
    order_index: int
    unlock_level: int
    xp_reward: int
    coin_reward: int
    is_boss: bool = False
    status: str = "locked"
    challenge_count: int = 0


class ChallengeDetail(BaseModel):
    id: int
    mission_id: int
    title: str
    description: str
    category: str
    difficulty: int
    validation_type: str
    objective: str
    xp_reward: int
    coin_reward: int
    hint_stage_1: str | None = None
    hint_stage_2: str | None = None
    hint_stage_3: str | None = None


class ChallengeSubmitRequest(BaseModel):
    code: str | None = None
    visual_program: list[str] | None = None
    maze_path: list[str] | None = None
    notes: str | None = None


class SubmitResult(BaseModel):
    success: bool
    message: str
    xp_awarded: int
    coins_awarded: int
    rank: str
    next_mission_unlocked: bool = False
    performance_score: int
    trace: list[dict[str, Any]] | None = None
    adaptive_difficulty: int | None = None


class HintResponse(BaseModel):
    challenge_id: int
    stage: int
    hint: str
    total_stages: int = 3


class ProgressionResponse(BaseModel):
    player_id: int
    xp: int
    coins: int
    rank: str
    completed_challenges: int
    unlocked_regions: int
    unlocked_missions: int
    current_region_id: int | None = None
    current_mission_id: int | None = None
    achievements: list[str]
    skills_unlocked: list[str]


class MasteryResponse(BaseModel):
    player_id: int
    overall_mastery: int
    by_category: dict[str, float]


class WorldResponse(BaseModel):
    regions: list[WorldRegion]
    missions: list[MissionSummary]


class MissionProgressEntry(BaseModel):
    mission_id: int
    status: str
    attempts: int
    best_score: int
    xp_earned: int
    coins_earned: int
