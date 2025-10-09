"""Ensure slide partner records never adjust karma."""

from odoo import models

from .no_karma_mixin import NoKarmaMixin


class SlideSlidePartner(NoKarmaMixin, models.Model):
    _inherit = "slide.slide.partner"

    def _update_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)
