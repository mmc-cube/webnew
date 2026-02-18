"""GitHub 星数历史追踪器 — 支持多周期涨星排行"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# 排行周期定义：(标签, 天数)
PERIODS = [
    ("daily", 1),
    ("weekly", 7),
    ("monthly", 30),
    ("3month", 90),
    ("6month", 180),
    ("9month", 270),
    ("yearly", 365),
]

MAX_HISTORY_DAYS = 400  # 保留最多 400 天历史，覆盖 yearly + 余量


class StarTracker:
    """持久化追踪 repo 星数，计算多周期涨星排行"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "star_history.json"
        self.history: dict[str, dict[str, int]] = self._load()

    def _load(self) -> dict:
        """加载历史数据 { "owner/repo": { "2026-02-18": 12345, ... } }"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Failed to load star_history.json: {e}")
        return {}

    def save(self):
        """保存历史数据"""
        self.history_file.write_text(
            json.dumps(self.history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update(self, repos: list[dict], date_str: str | None = None):
        """记录今天所有 repo 的星数"""
        today = date_str or datetime.now().strftime("%Y-%m-%d")
        for repo in repos:
            name = repo.get("name", "")
            stars = repo.get("stars", 0)
            if not name or not stars:
                continue
            if name not in self.history:
                self.history[name] = {}
            self.history[name][today] = stars

    def cleanup_old(self):
        """清理超过 MAX_HISTORY_DAYS 的旧数据"""
        cutoff = (datetime.now() - timedelta(days=MAX_HISTORY_DAYS)).strftime("%Y-%m-%d")
        for name in list(self.history.keys()):
            dates = self.history[name]
            old_keys = [d for d in dates if d < cutoff]
            for k in old_keys:
                del dates[k]
            if not dates:
                del self.history[name]

    def calc_growth(self, name: str, days: int, today: str | None = None) -> int | None:
        """计算某 repo 在指定天数内的涨星数，无历史数据返回 None"""
        today = today or datetime.now().strftime("%Y-%m-%d")
        dates = self.history.get(name, {})
        current = dates.get(today)
        if current is None:
            return None

        target_date = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")

        # 找最接近 target_date 的历史记录（前后 3 天容差）
        best_date = None
        best_diff = 999
        for d in dates:
            diff = abs((datetime.strptime(d, "%Y-%m-%d") - datetime.strptime(target_date, "%Y-%m-%d")).days)
            if diff < best_diff:
                best_diff = diff
                best_date = d

        if best_date is None or best_diff > 3:
            return None

        past_stars = dates[best_date]
        return current - past_stars

    def generate_leaderboards(self, top_n: int = 20, today: str | None = None) -> dict:
        """生成所有周期的排行榜

        Returns:
            {
                "daily": [{"name": "owner/repo", "stars": 12345, "growth": 500, "description": "", "language": ""}, ...],
                "weekly": [...],
                ...
            }
        """
        today = today or datetime.now().strftime("%Y-%m-%d")
        result = {}

        for label, days in PERIODS:
            entries = []
            for name, dates in self.history.items():
                current = dates.get(today)
                if current is None:
                    continue
                growth = self.calc_growth(name, days, today)
                if growth is not None and growth > 0:
                    entries.append({
                        "name": name,
                        "stars": current,
                        "growth": growth,
                    })

            entries.sort(key=lambda x: x["growth"], reverse=True)
            result[label] = entries[:top_n]

        return result
