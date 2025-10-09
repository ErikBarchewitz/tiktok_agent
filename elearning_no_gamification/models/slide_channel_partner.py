"""Disable karma rewards when completing channels."""

from odoo import models

from .no_karma_mixin import NoKarmaMixin


class SlideChannelPartner(NoKarmaMixin, models.Model):
    _inherit = "slide.channel.partner"

    def _post_completion_update_hook(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)
