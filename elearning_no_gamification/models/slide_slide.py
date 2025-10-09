"""Monkey patches for slide.slide to suppress karma operations."""

from odoo import _, models
from odoo.exceptions import UserError

from .no_karma_mixin import NoKarmaMixin


class SlideSlide(NoKarmaMixin, models.Model):
    _inherit = "slide.slide"

    def _action_set_quiz_done(self, completed=True):  # type: ignore[override]
        """Override to mark quizzes without touching karma."""
        if any(not slide.channel_id.is_member or not slide.website_published for slide in self):
            raise UserError(
                _('You cannot mark a slide quiz as completed if you are not among its members or it is unpublished.')
                if completed
                else _('You cannot mark a slide quiz as not completed if you are not among its members or it is unpublished.')
            )

        for slide in self:
            user_membership_sudo = slide.user_membership_id.sudo()
            if (
                not user_membership_sudo
                or user_membership_sudo.completed == completed
                or not user_membership_sudo.quiz_attempts_count
                or not slide.question_ids
            ):
                continue

            # keep the attempt counter logic untouched but skip karma updates entirely
            gains = [
                slide.quiz_first_attempt_reward,
                slide.quiz_second_attempt_reward,
                slide.quiz_third_attempt_reward,
                slide.quiz_fourth_attempt_reward,
            ]
            _ = gains[min(user_membership_sudo.quiz_attempts_count, len(gains)) - 1]
            # No karma update on purpose

        return True

    def _compute_quiz_info(self, target_partner, quiz_done=False):  # type: ignore[override]
        """Remove karma amounts from quiz info structures."""
        result = super()._compute_quiz_info(target_partner, quiz_done)
        if not result:
            return result
        for values in result.values():
            if isinstance(values, dict):
                values.update({
                    'quiz_karma_max': 0,
                    'quiz_karma_gain': 0,
                    'quiz_karma_won': 0,
                })
        return result

    def _action_vote(self, vote, upvote=True):  # type: ignore[override]
        """Keep voting functional but do not add karma when liking slides."""
        result = super()._action_vote(vote, upvote=upvote)
        return result
