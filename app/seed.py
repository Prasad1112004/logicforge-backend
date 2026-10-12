from __future__ import annotations

from datetime import datetime

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    ByteHintLog,
    Challenge,
    Mission,
    Player,
    PlayerAchievement,
    PlayerMissionProgress,
    Region,
)
from app.schemas import ChallengeSubmitRequest, HintResponse, MasteryResponse, ProgressionResponse
from app.visual_executor import execute_visual_program, validate_path_matches


def _rank_for_xp(xp: int) -> str:
    if xp >= 1500:
        return "Master Coder"
    if xp >= 1000:
        return "Senior Engineer"
    if xp >= 700:
        return "Problem Solver"
    if xp >= 400:
        return "Logic Ranger"
    if xp >= 200:
        return "Byte Apprentice"
    return "Rookie"


def _skills_for_xp(xp: int) -> list[str]:
    skills = []
    if xp >= 120:
        skills.append("Conditions")
    if xp >= 260:
        skills.append("Loops")
    if xp >= 450:
        skills.append("Arrays")
    if xp >= 700:
        skills.append("Functions")
    if xp >= 1000:
        skills.append("Debugging")
    if xp >= 1300:
        skills.append("Algorithms")
    return skills


def _award_achievement(db: Session, player: Player, code: str, name: str, description: str) -> None:
    existing = db.query(PlayerAchievement).filter_by(player_id=player.id, achievement_code=code).first()
    if existing:
        return
    db.add(
        PlayerAchievement(
            player_id=player.id,
            achievement_code=code,
            name=name,
            description=description,
        )
    )
    db.commit()


def _evaluate_keywords(challenge: Challenge, code: str) -> bool:
    if not code:
        return False
    tokens = [token.strip().lower() for token in code.replace("\n", " ").split() if token.strip()]
    if challenge.required_keywords:
        required = [keyword.strip().lower() for keyword in challenge.required_keywords.split(",")]
        return all(keyword in tokens for keyword in required)
    return True


def _evaluate_challenge_submission(challenge: Challenge, payload: ChallengeSubmitRequest) -> dict:
    if challenge.validation_type == "maze":
        if not payload.visual_program:
            raise ValueError("Maze challenge requires a visual_program list of instructions.")
        maze_map = {
            "start": (0, 0),
            "goal": (2, 2),
        }
        result = execute_visual_program(payload.visual_program, maze_map)
        expected = challenge.expected_path
        if expected:
            comparison = validate_path_matches(payload.visual_program, [item.strip() for item in expected.split(",")])
            success = comparison and result["success"]
        else:
            success = result["success"]
        return {
            "success": success,
            "trace": result["trace"],
            "message": "Maze route complete." if success else "The avatar did not reach the goal state.",
        }

    if not payload.code or not payload.code.strip():
        raise ValueError("A challenge submission requires code or instructions.")

    if challenge.validation_type in {"conditions", "loops", "arrays", "functions", "debugging", "algorithms"}:
        success = _evaluate_keywords(challenge, payload.code)
        return {
            "success": success,
            "trace": None,
            "message": "Challenge logic validated." if success else "The solution does not yet satisfy the challenge objective.",
        }

    return {
        "success": False,
        "trace": None,
        "message": "Unsupported challenge validation type.",
    }


def _unlock_next_mission(db: Session, player: Player) -> bool:
    next_mission = db.query(Mission).filter(Mission.id > (player.current_mission_id or 0)).order_by(Mission.id).first()
    if next_mission:
        player.current_mission_id = next_mission.id
        player.current_region_id = next_mission.region_id
        return True
    return False


def _build_mastery(db: Session, player: Player) -> MasteryResponse:
    total = db.query(Challenge).count()
    completed = player.completed_challenges
    categories = {"conditions": 0, "loops": 0, "arrays": 0, "functions": 0, "debugging": 0, "algorithms": 0, "maze": 0}
    by_category = {k: 0.0 for k in categories}
    for challenge in db.query(Challenge).all():
        if challenge.category in categories:
            by_category[challenge.category] = max(by_category[challenge.category], min(100, (challenge.difficulty * 12)))
    if completed > 0:
        overall_mastery = min(100, round((completed / max(total, 1)) * 100))
    else:
        overall_mastery = 0
    return MasteryResponse(player_id=player.id, overall_mastery=overall_mastery, by_category=by_category)


def create_guest_player(db: Session, guest_name: str | None) -> Player:
    import uuid

    guest_code = f"BYTE-{uuid.uuid4().hex[:8].upper()}"
    player = Player(
        guest_name=guest_name or "Guest",
        guest_code=guest_code,
        xp=0,
        coins=0,
        rank="Rookie",
        current_region_id=1,
        current_mission_id=1,
        performance_score=50,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def get_player_or_404(db: Session, player_id: int) -> Player:
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


def get_world_payload(db: Session) -> dict:
    regions = db.query(Region).order_by(Region.order_index).all()
    missions = db.query(Mission).order_by(Mission.region_id, Mission.order_index).all()
    return {"regions": regions, "missions": missions}


def get_player_progression(db: Session, player: Player) -> ProgressionResponse:
    unlocked_missions = db.query(PlayerMissionProgress).filter_by(player_id=player.id).count()
    unlocked_regions = db.query(Region).filter(Region.id <= (player.current_region_id or 1)).count()
    achievements = [entry.name for entry in db.query(PlayerAchievement).filter_by(player_id=player.id).all()]
    return ProgressionResponse(
        player_id=player.id,
        xp=player.xp,
        coins=player.coins,
        rank=player.rank,
        completed_challenges=player.completed_challenges,
        unlocked_regions=unlocked_regions,
        unlocked_missions=unlocked_missions,
        current_region_id=player.current_region_id,
        current_mission_id=player.current_mission_id,
        achievements=achievements,
        skills_unlocked=_skills_for_xp(player.xp),
    )


def submit_challenge_for_player(db: Session, player: Player, challenge_id: int, payload: ChallengeSubmitRequest) -> dict:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    result = _evaluate_challenge_submission(challenge, payload)
    success = bool(result.get("success"))
    if success:
        player.xp += challenge.xp_reward
        player.coins += challenge.coin_reward
        player.completed_challenges += 1
        player.performance_score = min(100, max(0, player.performance_score + 10))
        if player.current_mission_id == challenge.mission_id:
            progress = db.query(PlayerMissionProgress).filter_by(player_id=player.id, mission_id=challenge.mission_id).first()
            if progress is None:
                progress = PlayerMissionProgress(player_id=player.id, mission_id=challenge.mission_id)
                db.add(progress)
            progress.status = "completed"
            progress.attempts += 1
            progress.best_score = max(progress.best_score, 100)
            progress.completed_at = datetime.utcnow()
            progress.xp_earned += challenge.xp_reward
            progress.coins_earned += challenge.coin_reward

        player.rank = _rank_for_xp(player.xp)
        _award_achievement(db, player, "first_solve", "First Solve", "Solved your first coding challenge.")
        if player.xp >= 200:
            _award_achievement(db, player, "logic_ranger", "Logic Ranger", "Reached 200 XP.")
        if player.xp >= 700:
            _award_achievement(db, player, "problem_solver", "Problem Solver", "Reached 700 XP.")
        db.commit()
        db.refresh(player)
        next_unlocked = _unlock_next_mission(db, player)
        return {
            "success": True,
            "message": result["message"],
            "xp_awarded": challenge.xp_reward,
            "coins_awarded": challenge.coin_reward,
            "rank": player.rank,
            "next_mission_unlocked": next_unlocked,
            "performance_score": player.performance_score,
            "trace": result.get("trace"),
            "adaptive_difficulty": min(5, max(1, round(player.performance_score / 20))),
        }

    player.performance_score = max(0, player.performance_score - 5)
    db.commit()
    return {
        "success": False,
        "message": result["message"],
        "xp_awarded": 0,
        "coins_awarded": 0,
        "rank": player.rank,
        "next_mission_unlocked": False,
        "performance_score": player.performance_score,
        "trace": result.get("trace"),
        "adaptive_difficulty": min(5, max(1, round(player.performance_score / 20))),
    }


def generate_hint_for_player(db: Session, player: Player, challenge_id: int) -> HintResponse:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    logs = db.query(ByteHintLog).filter_by(player_id=player.id, challenge_id=challenge_id).all()
    last_stage = max((log.stage for log in logs), default=0)
    next_stage = min(3, last_stage + 1)
    messages = [
        challenge.hint_stage_1,
        challenge.hint_stage_2,
        challenge.hint_stage_3,
    ]
    hint = messages[next_stage - 1] or "Try breaking the problem into smaller steps and tracing the output one instruction at a time."
    db.add(ByteHintLog(player_id=player.id, challenge_id=challenge_id, stage=next_stage, message=hint))
    db.commit()
    return HintResponse(challenge_id=challenge_id, stage=next_stage, hint=hint, total_stages=3)


def _skills_for_xp(xp: int) -> list[str]:
    skills = []
    if xp >= 120:
        skills.append("Conditions")
    if xp >= 260:
        skills.append("Loops")
    if xp >= 450:
        skills.append("Arrays")
    if xp >= 700:
        skills.append("Functions")
    if xp >= 1000:
        skills.append("Debugging")
    if xp >= 1300:
        skills.append("Algorithms")
    return skills
