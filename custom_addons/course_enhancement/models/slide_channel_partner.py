from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class SlideChannelPartner(models.Model):
    _inherit = "slide.channel.partner"

    progress_percentage = fields.Float(
        string="Fortschritt",
        compute="_compute_progress_percentage",
        store=True,
        digits="Percentage",
    )

    @api.depends("completed_slide_ids", "channel_id.slide_ids")
    def _compute_progress_percentage(self):
        for attendee in self:
            total = len(attendee.channel_id.slide_ids)
            completed = len(attendee.completed_slide_ids)
            attendee.progress_percentage = (completed / total * 100.0) if total else 0.0

    @api.model
    def create(self, vals):
        if not self.env.user.has_group("base.group_user"):
            raise AccessError(
                _("Attendance can only be created by backend users. Please contact your course manager.")
            )
        return super().create(vals)
