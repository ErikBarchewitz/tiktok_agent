from odoo import api, fields, models


class SlideChannel(models.Model):
    """Extend eLearning courses with backend-centric defaults."""

    _inherit = "slide.channel"

    attendance_backend_only = fields.Boolean(
        string="Attendance in Backend",
        default=True,
        help="Restrict attendee registration to internal users only.",
    )
    default_template_id = fields.Many2one(
        "slide.content.template",
        string="Preferred Content Template",
        help="Default template suggested when new course content is created.",
    )
    participant_count = fields.Integer(
        string="Teilnehmer",
        compute="_compute_progress_metrics",
        store=True,
    )
    average_progress = fields.Float(
        string="Durchschnittlicher Fortschritt",
        compute="_compute_progress_metrics",
        store=True,
        digits="Percentage",
    )

    @api.model
    def create(self, vals):
        vals = self._apply_gamification_defaults(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._apply_gamification_defaults(vals)
        return super().write(vals)

    def _apply_gamification_defaults(self, vals):
        """Force gamification and karma features to stay disabled."""
        disabled_fields = [
            field_name
            for field_name in (
                "use_karma",
                "karma_enabled",
                "allow_rating",
                "enable_gamification",
                "karma_reward",
                "karma_gen_slide_channel",
                "use_karma_email_template",
            )
            if field_name in self._fields
        ]
        for field_name in disabled_fields:
            vals[field_name] = False
        return vals

    @api.depends("channel_partner_ids", "channel_partner_ids.progress_percentage")
    def _compute_progress_metrics(self):
        for channel in self:
            partners = channel.channel_partner_ids
            channel.participant_count = len(partners)
            if partners:
                channel.average_progress = sum(partners.mapped("progress_percentage")) / len(partners)
            else:
                channel.average_progress = 0.0

    def action_view_participant_progress(self):
        action = self.env.ref("course_enhancement.action_course_partner_progress").read()[0]
        action["domain"] = [("channel_id", "=", self.id)]
        action["context"] = dict(self.env.context, default_channel_id=self.id)
        return action
