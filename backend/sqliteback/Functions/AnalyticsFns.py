"""
Functions/AnalyticsFns.py — aggregate dashboard activity and dated profile chips.
"""

import datetime
import threading
import time
from collections import Counter
from typing import Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB

_DASHBOARD_CACHE: dict[tuple[int, int], tuple[float, dict]] = {}
_DASHBOARD_LOCK = threading.Lock()
_DASHBOARD_TTL = 15.0


def invalidate_analytics_cache(user_id: Optional[int] = None) -> None:
    with _DASHBOARD_LOCK:
        if user_id is None:
            _DASHBOARD_CACHE.clear()
        else:
            to_del = [k for k in _DASHBOARD_CACHE if k[0] == user_id]
            for k in to_del:
                _DASHBOARD_CACHE.pop(k, None)


class AnalyticsFns:
    def __init__(self, db: Database = DB):
        self.db = db
        self.posts = db.use("posts")
        self.profiles = db.use("profiles")
        self.chips = db.use("chips")

    def dashboard(self, user_id: int, days: int = 30) -> dict:
        days = max(7, min(days, 365))
        now = time.monotonic()
        cache_key = (user_id, days)
        with _DASHBOARD_LOCK:
            cached = _DASHBOARD_CACHE.get(cache_key)
            if cached is not None and now < cached[0]:
                return dict(cached[1])

        profile_row = self.profiles.query().where(user_id=user_id).first()
        if profile_row is None:
            raise LookupError("Profile not found.")
        profile_id = profile_row.id

        authored_posts = [row.to_model() for row in self.posts.query().where(user_id=user_id).all()]
        posts = [post for post in authored_posts if not post.is_comment]
        comments = [post for post in authored_posts if post.is_comment]
        post_ids = [post.id for post in authored_posts if post.id is not None]

        reaction_counts: Counter[str] = Counter()
        daily_posts: Counter[datetime.date] = Counter()
        for p in authored_posts:
            daily_posts[p.created_at.date()] += 1

        daily_reactions: Counter[datetime.date] = Counter()
        post_reaction_map: Counter[int] = Counter()
        if post_ids:
            for row in self.chips.query().where(chipped_to=post_ids, kind="reaction").all():
                chip = row.to_model()
                if not chip.content.startswith("profile:"):
                    reaction_counts[chip.content] += 1
                    post_reaction_map[chip.chipped_to] += 1
                    daily_reactions[chip.created_at.date()] += 1

        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=days - 1)
        daily: dict[datetime.date, dict[str, int]] = {}
        totals_before = {"follow": 0, "star": 0}

        relationship_chips = self.chips.query().where(
            chipped_to=profile_id,
            kind=["follow", "star"],
        ).all()
        for row in relationship_chips:
            chip = row.to_model()
            event_date = chip.created_at.date()
            if event_date < start_date:
                totals_before[chip.kind] += 1
            elif event_date <= end_date:
                day_counts = daily.setdefault(event_date, {"follow": 0, "star": 0})
                day_counts[chip.kind] += 1

        series = []
        cumulative_followers = totals_before["follow"]
        cumulative_stars = totals_before["star"]
        for offset in range(days):
            date = start_date + datetime.timedelta(days=offset)
            day_counts = daily.get(date, {"follow": 0, "star": 0})
            cumulative_followers += day_counts["follow"]
            cumulative_stars += day_counts["star"]
            series.append(
                {
                    "date": date.isoformat(),
                    "followers": cumulative_followers,
                    "stars": cumulative_stars,
                    "posts": daily_posts.get(date, 0),
                    "reactions": daily_reactions.get(date, 0),
                }
            )

        dominant_reaction, dominant_reaction_count = reaction_counts.most_common(1)[0] if reaction_counts else (None, 0)
        total_rx = sum(reaction_counts.values())

        post_comment_map: Counter[int] = Counter()
        if post_ids:
            for c in self.posts.query().where(reply_to=post_ids, is_comment=True).all():
                cm = c.to_model()
                post_comment_map[cm.reply_to] += 1

        top_posts = []
        ranked_posts = sorted(
            posts,
            key=lambda p: (post_reaction_map.get(p.id, 0) + post_comment_map.get(p.id, 0), p.created_at),
            reverse=True,
        )
        for p in ranked_posts[:5]:
            clean_text = " ".join(p.content.split())
            top_posts.append({
                "id": p.id,
                "content": clean_text[:100] + ("..." if len(clean_text) > 100 else ""),
                "reactions": post_reaction_map.get(p.id, 0),
                "comments": post_comment_map.get(p.id, 0),
                "created_at": p.created_at.isoformat(),
            })

        total_followers = sum(1 for row in relationship_chips if getattr(row, "kind", None) == "follow")
        total_stars = sum(1 for row in relationship_chips if getattr(row, "kind", None) == "star")
        total_following = self.chips.query().where(chipped_by=profile_id, kind="follow").count()
        engagement_rate = round((total_rx + len(comments)) / max(len(posts), 1), 2)

        result = {
            "days": days,
            "total_posts": len(posts),
            "total_comments": len(comments),
            "total_reactions": total_rx,
            "dominant_reaction": dominant_reaction,
            "dominant_reaction_count": dominant_reaction_count,
            "time_series": series,
            "reaction_breakdown": dict(reaction_counts),
            "total_followers": total_followers,
            "total_stars": total_stars,
            "total_following": total_following,
            "engagement_rate": engagement_rate,
            "top_posts": top_posts,
        }
        with _DASHBOARD_LOCK:
            _DASHBOARD_CACHE[cache_key] = (now + _DASHBOARD_TTL, result)
        return result
