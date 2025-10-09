"""Ensure survey hooks never reward karma."""

from odoo import models

from .no_karma_mixin import NoKarmaMixin


class SurveyUserInput(NoKarmaMixin, models.Model):
    _inherit = "survey.user_input"

    def _reward_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)
