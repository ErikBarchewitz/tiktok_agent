"""Helper mixin to centralize the karma suppression logic."""

from odoo import models


class NoKarmaMixin:
    """Mixin that provides helpers returning falsy values for karma hooks."""

    def _suppress_karma(self, *args, **kwargs):
        """Return ``False`` so caller can abort karma mutations."""
        return False

    def _suppress_karma_zero(self, *args, **kwargs):
        """Return ``0`` for hooks that expect a numeric karma delta."""
        return 0


class NoKarmaModelMixin(NoKarmaMixin, models.AbstractModel):
    """Abstract model to expose the helpers as model methods."""

    _name = "elearning.no.karma.mixin"
    _description = "eLearning mixin to disable karma side effects"

    def _suppress_karma(self, *args, **kwargs):  # type: ignore[override]
        return super()._suppress_karma(*args, **kwargs)

    def _suppress_karma_zero(self, *args, **kwargs):  # type: ignore[override]
        return super()._suppress_karma_zero(*args, **kwargs)
