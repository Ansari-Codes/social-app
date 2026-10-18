"""
Functions/ChipFns.py — follow, star, and reaction chip operations.
"""

from typing import Literal, Optional

from backend.sqliteback.Database.core import Database
from backend.sqliteback.Database.db import DB, Chip, Profile
from backend.sqliteback.Functions.NotificationFns import NotificationFns

ProfileChipKind = Literal["follow", "star"]


class ChipFns:
    def __init__(self, db: Database = DB):
        self.profiles = db.use("profiles")
        self.chips = db.use("chips")
        self.notifications = NotificationFns(db)

    def _profile(self, user_id: int):
        profile = self.profiles.query().where(user_id=user_id).first()
        if profile is None:
            raise LookupError("Profile not found.")
        return profile

    def set_profile_chip(
        self,
        chipped_by_user_id: int,
        chipped_to_user_id: int,
        kind: ProfileChipKind,
        enabled: bool,
    ) -> bool:
        actor = self._profile(chipped_by_user_id)
        target = self._profile(chipped_to_user_id)
        if actor.id == target.id:
            raise ValueError("You cannot follow or star your own profile.")

        existing = self.chips.query().where(
            chipped_by=actor.id,
            chipped_to=target.id,
            kind=kind,
        ).first()
        if enabled and existing is None:
            self.chips.insert(
                Chip(
                    chipped_by=actor.id,
                    chipped_to=target.id,
                    kind=kind,
                    content="",
                )
            )
            self.notifications.notify(
                chipped_to_user_id,
                kind,
                "followed your profile." if kind == "follow" else "starred your profile.",
                actor_user_id=chipped_by_user_id,
                target_type="profile",
                target_id=actor.id,
            )
        elif not enabled and existing is not None:
            self.chips.query().where(
                chipped_by=actor.id,
                chipped_to=target.id,
                kind=kind,
            ).delete()
        return enabled

    def profile_state(
        self,
        viewer_user_id: int | None,
        target_user_id: int,
        profiles_by_user_id: Optional[dict[int, Profile]] = None,
    ) -> dict:
        return self.profile_states(
            viewer_user_id, [target_user_id], profiles_by_user_id=profiles_by_user_id
        )[target_user_id]

    def profile_states(
        self,
        viewer_user_id: int | None,
        target_user_ids: list[int] | set[int],
        profiles_by_user_id: Optional[dict[int, Profile]] = None,
    ) -> dict[int, dict]:
        targets = set(target_user_ids)
        if not targets:
            return {}

        needed_user_ids = targets | ({viewer_user_id} if viewer_user_id is not None else set())
        profiles = dict(profiles_by_user_id or {})
        missing_user_ids = needed_user_ids - profiles.keys()
        if missing_user_ids:
            rows = self.profiles.query().where(user_id=list(missing_user_ids)).all()
            profiles.update({row.user_id: row.to_model() for row in rows})

        profile_ids = {
            user_id: profile.id
            for user_id, profile in profiles.items()
            if user_id in targets and profile.id is not None
        }
        if len(profile_ids) != len(targets):
            raise LookupError("Profile not found.")

        user_id_by_profile_id = {
            profile_id: user_id for user_id, profile_id in profile_ids.items()
        }
        viewer_profile = profiles.get(viewer_user_id) if viewer_user_id is not None else None
        viewer_profile_id = viewer_profile.id if viewer_profile is not None else None
        target_profile_ids = list(user_id_by_profile_id)

        states = {
            user_id: {
                "followers": 0,
                "following": 0,
                "stars": 0,
                "followed_by_me": False,
                "starred_by_me": False,
                "reactions": {},
                "my_reactions": set(),
            }
            for user_id in targets
        }

        incoming = self.chips.query().where(
            chipped_to=target_profile_ids,
            kind=["follow", "star", "reaction"],
        ).all()
        outgoing_follows = self.chips.query().where(
            chipped_by=target_profile_ids,
            kind="follow",
        ).all()

        for row in incoming:
            chip = row.to_model()
            user_id = user_id_by_profile_id.get(chip.chipped_to)
            if user_id is None:
                continue
            state = states[user_id]
            if chip.kind == "follow":
                state["followers"] += 1
                if chip.chipped_by == viewer_profile_id:
                    state["followed_by_me"] = True
            elif chip.kind == "star":
                state["stars"] += 1
                if chip.chipped_by == viewer_profile_id:
                    state["starred_by_me"] = True
            elif chip.content.startswith("profile:"):
                reaction = chip.content.removeprefix("profile:")
                state["reactions"][reaction] = state["reactions"].get(reaction, 0) + 1
                if chip.chipped_by == viewer_profile_id:
                    state["my_reactions"].add(reaction)

        for row in outgoing_follows:
            chip = row.to_model()
            user_id = user_id_by_profile_id.get(chip.chipped_by)
            if user_id is not None:
                states[user_id]["following"] += 1

        for state in states.values():
            state["my_reactions"] = sorted(state["my_reactions"])
        return states

    def profile_reactions(self, viewer_user_id: int | None, target_user_id: int) -> dict:
        target = self._profile(target_user_id)
        viewer_profile_id = (
            self._profile(viewer_user_id).id if viewer_user_id is not None else None
        )
        counts: dict[str, int] = {}
        mine: list[str] = []
        for chip in self.chips.query().where(chipped_to=target.id, kind="reaction").all():
            if not chip.content.startswith("profile:"):
                continue
            reaction = chip.content.removeprefix("profile:")
            counts[reaction] = counts.get(reaction, 0) + 1
            if chip.chipped_by == viewer_profile_id:
                mine.append(reaction)
        return {"reactions": counts, "my_reactions": sorted(mine)}

    def toggle_profile_reaction(
        self,
        chipped_by_user_id: int,
        chipped_to_user_id: int,
        content: str,
    ) -> dict:
        """Toggle a profile reaction; the prefix disambiguates overlapping table IDs."""
        actor = self._profile(chipped_by_user_id)
        target = self._profile(chipped_to_user_id)
        reaction = content.strip()
        if not reaction or len(reaction) > 32:
            raise ValueError("Reaction must contain 1 to 32 characters.")
        content = f"profile:{reaction}"

        existing = self.chips.query().where(
            chipped_by=actor.id,
            chipped_to=target.id,
            kind="reaction",
            content=content,
        ).first()
        if existing is None:
            self.chips.insert(
                Chip(
                    chipped_by=actor.id,
                    chipped_to=target.id,
                    kind="reaction",
                    content=content,
                )
            )
            self.notifications.notify(
                chipped_to_user_id,
                "reaction",
                f"reacted {reaction} to your profile.",
                actor_user_id=chipped_by_user_id,
                target_type="profile",
                target_id=actor.id,
            )
        else:
            self.chips.query().where(
                chipped_by=actor.id,
                chipped_to=target.id,
                kind="reaction",
                content=content,
            ).delete()
        return self.profile_reactions(chipped_by_user_id, chipped_to_user_id)

    def connection_profile_ids(self, user_id: int, direction: Literal["followers", "following"]) -> list[int]:
        target = self._profile(user_id)
        if direction == "followers":
            rows = self.chips.query().where(chipped_to=target.id, kind="follow").all()
            return [row.chipped_by for row in rows]
        rows = self.chips.query().where(chipped_by=target.id, kind="follow").all()
        return [row.chipped_to for row in rows]
