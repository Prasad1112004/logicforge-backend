from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.game_service import (
    create_guest_player,
    generate_hint_for_player,
    get_player_or_404,
    get_player_progression,
    get_world_payload,
    submit_challenge_for_player,
)
from app.models import Challenge, Mission, Player, Region
from app.schemas import ChallengeDetail, ChallengeSubmitRequest, HintResponse, MasteryResponse, PlayerCreateRequest, PlayerResponse, ProgressionResponse, WorldResponse

router = APIRouter()


def get_current_player(
    x_player_id: int | None = Header(default=None, alias="X-Player-ID"),
    db: Session = Depends(get_db),
) -> Player:
    if x_player_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Player session required")
    return get_player_or_404(db, x_player_id)


@router.post("/players/guest", response_model=PlayerResponse)
def create_player_endpoint(payload: PlayerCreateRequest, db: Session = Depends(get_db)) -> Player:
    player = create_guest_player(db, payload.guest_name)
    return PlayerResponse(
        id=player.id,
        guest_name=player.guest_name,
        guest_code=player.guest_code,
        xp=player.xp,
        coins=player.coins,
        rank=player.rank,
        current_region_id=player.current_region_id,
        current_mission_id=player.current_mission_id,
        performance_score=player.performance_score,
        completed_challenges=player.completed_challenges,
    )


@router.get("/players/me", response_model=PlayerResponse)
def get_current_player_endpoint(player: Player = Depends(get_current_player)) -> PlayerResponse:
    return PlayerResponse(
        id=player.id,
        guest_name=player.guest_name,
        guest_code=player.guest_code,
        xp=player.xp,
        coins=player.coins,
        rank=player.rank,
        current_region_id=player.current_region_id,
        current_mission_id=player.current_mission_id,
        performance_score=player.performance_score,
        completed_challenges=player.completed_challenges,
    )


@router.get("/world", response_model=WorldResponse)
def get_world(db: Session = Depends(get_db)) -> WorldResponse:
    payload = get_world_payload(db)
    regions = [
        {"id": region.id, "name": region.name, "description": region.description, "theme": region.theme, "order_index": region.order_index}
        for region in payload["regions"]
    ]
    missions = [
        {
            "id": mission.id,
            "region_id": mission.region_id,
            "title": mission.title,
            "description": mission.description,
            "mission_type": mission.mission_type,
            "order_index": mission.order_index,
            "unlock_level": mission.unlock_level,
            "xp_reward": mission.xp_reward,
            "coin_reward": mission.coin_reward,
            "is_boss": mission.is_boss,
            "status": "unlocked",
            "challenge_count": len(mission.challenges),
        }
        for mission in payload["missions"]
    ]
    return WorldResponse(regions=regions, missions=missions)


@router.get("/missions")
def list_missions(db: Session = Depends(get_db)) -> list[dict]:
    missions = db.query(Mission).order_by(Mission.region_id, Mission.order_index).all()
    output = []
    for mission in missions:
        output.append(
            {
                "id": mission.id,
                "region_id": mission.region_id,
                "title": mission.title,
                "description": mission.description,
                "mission_type": mission.mission_type,
                "unlock_level": mission.unlock_level,
                "xp_reward": mission.xp_reward,
                "coin_reward": mission.coin_reward,
                "is_boss": mission.is_boss,
                "challenge_count": len(mission.challenges),
            }
        )
    return output


@router.get("/challenges/{challenge_id}", response_model=ChallengeDetail)
def get_challenge_detail(challenge_id: int, db: Session = Depends(get_db)) -> Challenge:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    return ChallengeDetail(
        id=challenge.id,
        mission_id=challenge.mission_id,
        title=challenge.title,
        description=challenge.description,
        category=challenge.category,
        difficulty=challenge.difficulty,
        validation_type=challenge.validation_type,
        objective=challenge.objective,
        xp_reward=challenge.xp_reward,
        coin_reward=challenge.coin_reward,
        hint_stage_1=challenge.hint_stage_1,
        hint_stage_2=challenge.hint_stage_2,
        hint_stage_3=challenge.hint_stage_3,
    )


@router.post("/challenges/{challenge_id}/submit")
def submit_challenge(challenge_id: int, payload: ChallengeSubmitRequest, db: Session = Depends(get_db), player: Player = Depends(get_current_player)) -> dict:
    result = submit_challenge_for_player(db, player, challenge_id, payload)
    return result


@router.post("/challenges/{challenge_id}/hint", response_model=HintResponse)
def request_hint(challenge_id: int, db: Session = Depends(get_db), player: Player = Depends(get_current_player)) -> HintResponse:
    return generate_hint_for_player(db, player, challenge_id)


@router.get("/progression", response_model=ProgressionResponse)
def get_progression(player: Player = Depends(get_current_player), db: Session = Depends(get_db)) -> ProgressionResponse:
    return get_player_progression(db, player)


@router.get("/learning/mastery")
def get_mastery(player: Player = Depends(get_current_player), db: Session = Depends(get_db)) -> dict:
    categories = {
        "conditions": 55 if player.completed_challenges > 0 else 0,
        "loops": 50 if player.completed_challenges > 1 else 0,
        "arrays": 40 if player.completed_challenges > 2 else 0,
        "functions": 35 if player.completed_challenges > 3 else 0,
        "debugging": 30 if player.completed_challenges > 4 else 0,
        "algorithms": 25 if player.completed_challenges > 5 else 0,
        "maze": 20 if player.completed_challenges > 6 else 0,
    }
    overall = min(100, int(sum(categories.values()) / len(categories)))
    return {"player_id": player.id, "overall_mastery": overall, "by_category": categories}
