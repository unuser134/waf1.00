"""配置校验工具，启动时提前发现配置错误。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, validator


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    access_log: str = Field(default="logs/access.log")
    error_log: str = Field(default="logs/error.log")
    blocked_log: str = Field(default="logs/blocked.log")
    max_size: str = Field(default="100MB")
    backup_count: int = Field(default=5, ge=1, le=50)

    @validator("level")
    def validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"logging.level 必须是 {allowed} 之一")
        return upper


class ServerConfig(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080, ge=1, le=65535)
    workers: int = Field(default=1, ge=1, le=64)
    timeout: int = Field(default=30, ge=1, le=600)
    max_request_size: str = Field(default="10MB")


class RulesConfig(BaseModel):
    auto_reload: bool = Field(default=False)
    reload_interval: int = Field(default=300, ge=0)
    directories: List[str] = Field(default_factory=list)

    @validator("directories", each_item=True)
    def validate_rule_paths(cls, v: str) -> str:
        if not v:
            raise ValueError("规则文件路径不能为空")
        return v


class WhitelistConfig(BaseModel):
    enabled: bool = Field(default=True)
    file: Optional[str] = None


class BlockingConfig(BaseModel):
    enabled: bool = Field(default=True)
    response_code: int = Field(default=403, ge=100, le=599)
    response_message: str = Field(default="Request blocked by WAF")


class DetectionConfig(BaseModel):
    enabled: bool = Field(default=True)
    rule_matching: bool = Field(default=True)
    signature_matching: bool = Field(default=True)
    anomaly_detection: bool = Field(default=False)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    cache_ttl_seconds: int = Field(default=5, ge=0, le=3600)


class WAFConfig(BaseModel):
    name: str = Field(default="TraditionalWAF")
    version: str = Field(default="1.0.0")
    mode: str = Field(default="protection")

    @validator("mode")
    def validate_mode(cls, v: str) -> str:
        if v not in {"protection", "detection"}:
            raise ValueError("waf.mode 必须是 protection 或 detection")
        return v


class Settings(BaseModel):
    waf: WAFConfig = Field(default_factory=WAFConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    whitelist: WhitelistConfig = Field(default_factory=WhitelistConfig)
    blocking: BlockingConfig = Field(default_factory=BlockingConfig)


def load_and_validate_config(path: str) -> Settings:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    import yaml

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    try:
        return Settings(**data)
    except ValidationError as exc:
        raise ValueError(f"配置校验失败: {exc}") from exc
