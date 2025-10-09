"""Overrides for ``res.users`` to neutralise karma adjustments."""

from odoo import models

from .no_karma_mixin import NoKarmaMixin


class ResUsers(NoKarmaMixin, models.Model):
    """Disable all public hooks adding or removing karma."""

    _inherit = "res.users"

    def add_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _add_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _add_karma_batch(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _increase_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _decrease_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _update_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)

    def _set_karma(self, *args, **kwargs):  # type: ignore[override]
        return self._suppress_karma(*args, **kwargs)
