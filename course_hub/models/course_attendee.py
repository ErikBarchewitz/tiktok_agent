# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CourseAttendee(models.Model):
    _name = "course.attendee"
    _description = "Course Attendee"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "enrollment_date desc"

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    course_id = fields.Many2one(
        "course.course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    enrollment_date = fields.Datetime(
        default=fields.Datetime.now,
        tracking=True,
    )
    completed_content_ids = fields.Many2many(
        "course.content",
        "course_attendee_content_rel",
        "attendee_id",
        "content_id",
        string="Completed Content",
    )
    progress = fields.Float(
        compute="_compute_progress",
        store=True,
        digits=(16, 2),
    )
    progress_label = fields.Char(compute="_compute_progress", store=True)
    notes = fields.Text()
    state = fields.Selection(
        [
            ("draft", "Entwurf"),
            ("in_progress", "Aktiv"),
            ("done", "Abgeschlossen"),
        ],
        default="draft",
        tracking=True,
    )

    _sql_constraints = [
        (
            "course_attendee_unique",
            "unique(partner_id, course_id)",
            "A partner can only attend the same course once.",
        )
    ]

    @api.depends("completed_content_ids", "course_id.total_content")
    def _compute_progress(self):
        for attendee in self:
            total = attendee.course_id.total_content
            completed = len(attendee.completed_content_ids)
            attendee.progress = total and (completed / total) * 100 or 0.0
            attendee.progress_label = f"{attendee.progress:.0f}%" if total else "0%"
            attendee.state = (
                "done"
                if attendee.progress >= 100
                else "in_progress"
                if attendee.progress > 0
                else "draft"
            )

    def action_mark_content_complete(self, content_id):
        self.ensure_one()
        content = self.env["course.content"].browse(content_id)
        if content and content not in self.completed_content_ids:
            self.completed_content_ids = [(4, content.id)]
        return True

    def action_reset_progress(self):
        for attendee in self:
            attendee.completed_content_ids = [(5, 0, 0)]
