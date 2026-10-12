from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    guest_name: Mapped[str] = mapped_column(String(80), default="Guest")
    guest_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    coins: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[str] = mapped_column(String(40), default="Rookie")
    current_region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.id"), nullable=True)
    current_mission_id: Mapped[int | None] = mapped_column(ForeignKey("missions.id"), nullable=True)
    performance_score: Mapped[int] = mapped_column(Integer, default=50)
    completed_challenges: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mission_progress: Mapped[list["PlayerMissionProgress"]] = relationship(back_populates="player")
    achievements: Mapped[list["PlayerAchievement"]] = relationship(back_populates="player")
    hint_logs: Mapped[list["ByteHintLog"]] = relationship(back_populates="player")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=1)
    theme: Mapped[str | None] = mapped_column(String(80), nullable=True)

    missions: Mapped[list["Mission"]] = relationship(back_populates="region")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mission_type: Mapped[str] = mapped_column(String(40), default="practice")
    order_index: Mapped[int] = mapped_column(Integer, default=1)
    unlock_level: Mapped[int] = mapped_column(Integer, default=1)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    coin_reward: Mapped[int] = mapped_column(Integer, default=0)
    story_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_boss: Mapped[bool] = mapped_column(Boolean, default=False)

    region: Mapped[Region] = relationship(back_populates="missions")
    challenges: Mapped[list["Challenge"]] = relationship(back_populates="mission")
    player_progress: Mapped[list["PlayerMissionProgress"]] = relationship(back_populates="mission")


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="conditions")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    validation_type: Mapped[str] = mapped_column(String(40), default="keywords")
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    required_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_program: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint_stage_1: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint_stage_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint_stage_3: Mapped[str | None] = mapped_column(Text, nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=25)
    coin_reward: Mapped[int] = mapped_column(Integer, default=10)
    is_boss_phase: Mapped[bool] = mapped_column(Boolean, default=False)
    boss_phase: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mission: Mapped[Mission] = relationship(back_populates="challenges")


class PlayerMissionProgress(Base):
    __tablename__ = "player_mission_progress"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="locked")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    coins_earned: Mapped[int] = mapped_column(Integer, default=0)

    player: Mapped[Player] = relationship(back_populates="mission_progress")
    mission: Mapped[Mission] = relationship(back_populates="player_progress")


class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    achievement_code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped[Player] = relationship(back_populates="achievements")


class ByteHintLog(Base):
    __tablename__ = "byte_hint_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    stage: Mapped[int] = mapped_column(Integer, default=1)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped[Player] = relationship(back_populates="hint_logs")
