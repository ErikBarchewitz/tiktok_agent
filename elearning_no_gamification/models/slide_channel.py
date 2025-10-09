"""Karma overrides for ``slide.channel`` objects."""

from collections import defaultdict

from odoo import models

from .no_karma_mixin import NoKarmaMixin


class SlideChannel(NoKarmaMixin, models.Model):
    _inherit = "slide.channel"

    def _post_completion_update_hook(self, completed=True):  # type: ignore[override]
        """Block karma gain when members finish or reopen a course."""
        return self._suppress_karma(completed)

    def _get_earned_karma(self, partner_ids):  # type: ignore[override]
        """Return empty karma history so leaderboards stay blank."""
        _ = partner_ids
        return defaultdict(list)

    def _compute_action_rights(self):  # type: ignore[override]
        """Allow voting/commenting/reviewing without karma thresholds."""
        for channel in self:
            if channel.can_publish:
                channel.can_vote = channel.can_comment = channel.can_review = True
            elif not channel.is_member:
                channel.can_vote = channel.can_comment = channel.can_review = False
            else:
                channel.can_vote = channel.can_comment = channel.can_review = True
        return None
