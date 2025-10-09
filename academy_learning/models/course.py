# -*- coding: utf-8 -*-
"""Enhancements to the core eLearning course model."""

from odoo import api, fields, models


class SlideChannel(models.Model):
    """Extend the standard course model to add analytics friendly fields."""

    _inherit = "slide.channel"

    academy_section_ids = fields.One2many(
        "academy.course.section",
        "channel_id",
        string="Learning Sections",
        help="Structured sections that group learning content.",
    )
    academy_enrollment_ids = fields.One2many(
        "academy.course.enrollment",
        "channel_id",
        string="Enrollments",
    )
    allow_self_enroll = fields.Boolean(
        string="Allow Self Enrollment",
        default=True,
        help="When enabled, users can enrol themselves from the website.",
    )
    total_duration = fields.Float(
        string="Total Duration (minutes)",
        compute="_compute_total_duration",
        store=True,
    )
    active_enrollment_count = fields.Integer(
        compute="_compute_enrollment_stats",
        string="Active Enrollments",
        store=False,
    )
    average_completion_ratio = fields.Float(
        compute="_compute_enrollment_stats",
        string="Average Completion",
        store=False,
    )

    def _compute_total_duration(self):
        """Aggregate the estimated duration across all sections."""
        for channel in self:
            duration = sum(channel.slide_ids.mapped("completion_time"))
            section_duration = sum(channel.academy_section_ids.mapped("estimated_duration"))
            channel.total_duration = duration + section_duration

    def _compute_enrollment_stats(self):
        for channel in self:
            enrollments = channel.academy_enrollment_ids.filtered(lambda e: e.state == "active")
            channel.active_enrollment_count = len(enrollments)
            if enrollments:
                channel.average_completion_ratio = sum(enrollments.mapped("completion_ratio")) / len(
                    enrollments
                )
            else:
                channel.average_completion_ratio = 0.0

    def action_open_player(self):
        """Return an action for launching the learning player."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/academy/course/%s" % self.id,
        }

    def _cron_update_time_spent(self):
        """Scheduled job to refresh time spent statistics."""
        enrollments = self.env["academy.course.enrollment"].search([("state", "=", "active")])
        enrollments._recompute_time_spent()
        return True


class SlideSlide(models.Model):
    """Extend slide slides to provide richer metadata."""

    _inherit = "slide.slide"

    academy_content_id = fields.Many2one("academy.course.content", string="Academy Content")
    completion_time = fields.Float(
        string="Estimated Completion (minutes)",
        default=5,
        help="Soft metric used to calculate total course effort.",
    )
    is_visible_in_player = fields.Boolean(
        string="Show in Player",
        default=True,
        help="Allows hiding supporting assets from the learner navigation.",
    )


class ResUsers(models.Model):
    """Add quick access helper fields on users."""

    _inherit = "res.users"

    academy_enrollment_ids = fields.One2many(
        "academy.course.enrollment", "user_id", string="Academy Enrollments"
    )

    def action_view_academy_courses(self):
        self.ensure_one()
        action = self.env.ref("website_slides.slide_channel_action").read()[0]
        action["domain"] = [
            "|",
            ("user_id", "=", self.id),
            ("academy_enrollment_ids.user_id", "=", self.id),
        ]
        return action
