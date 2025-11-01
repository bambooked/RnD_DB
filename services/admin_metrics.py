"""管理者向けメトリクスの簡易永続化ユーティリティ"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional


class AdminMetricsStore:
    """LLM使用量やメンテナンスイベントをシンプルに蓄積するストア"""

    def __init__(self, path: Optional[str] = None, max_events: int = 100) -> None:
        self.path = path or os.getenv("ADMIN_METRICS_PATH", "data/admin_metrics.json")
        self.max_events = max_events
        self._lock = threading.Lock()
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.path):
            self._save({
                "llm_usage": {
                    "total_calls": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_tokens": 0,
                    "per_model": {}
                },
                "events": []
            })

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "llm_usage": {
                    "total_calls": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_tokens": 0,
                    "per_model": {}
                },
                "events": []
            }

    def _save(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_llm_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: Optional[int] = None,
    ) -> None:
        with self._lock:
            data = self._load()
            usage = data.setdefault("llm_usage", {
                "total_calls": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "per_model": {}
            })

            usage["total_calls"] += 1
            usage["total_prompt_tokens"] += max(prompt_tokens or 0, 0)
            usage["total_completion_tokens"] += max(completion_tokens or 0, 0)
            total = total_tokens if total_tokens is not None else (prompt_tokens or 0) + (completion_tokens or 0)
            usage["total_tokens"] += max(total, 0)

            per_model = usage.setdefault("per_model", {})
            model_stats = per_model.setdefault(model, {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
            model_stats["calls"] += 1
            model_stats["prompt_tokens"] += max(prompt_tokens or 0, 0)
            model_stats["completion_tokens"] += max(completion_tokens or 0, 0)
            model_stats["total_tokens"] += max(total, 0)

            self._save(data)

    def record_event(
        self,
        event_type: str,
        status: str,
        message: str,
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            data = self._load()
            events = data.setdefault("events", [])
            entry: Dict[str, Any] = {
                "type": event_type,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
            if extra:
                entry["details"] = extra
            events.append(entry)
            if len(events) > self.max_events:
                events[:] = events[-self.max_events:]
            self._save(data)

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
        return data


# 共有インスタンス
admin_metrics = AdminMetricsStore()

