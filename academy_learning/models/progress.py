# -*- coding: utf-8 -*-
"""Progress entries for tracking learner advancement."""

from odoo import fields, models


class AcademyCourseProgress(models.Model):
    _name = "academy.course.progress"
    _description = "Learner Progress"
    _order = "content_sequence, id"

    enrollment_id = fields.Many2one("academy.course.enrollment", required=True, ondelete="cascade")
    content_id = fields.Many2one("academy.course.content", required=True, ondelete="cascade")
    is_completed = fields.Boolean(default=False)
    latest_score = fields.Float(default=0.0)
    time_spent = fields.Float(default=0.0, help="Minutes spent on this content.")
    content_sequence = fields.Integer(related="content_id.sequence", store=True)

    _sql_constraints = [
        (
            "academy_unique_progress_entry",
            "unique(enrollment_id, content_id)",
            "Content progress must be unique per enrolment.",
        )
    ]

    def toggle_complete(self):
        for record in self:
            record.is_completed = not record.is_completed
            record.enrollment_id._update_completion()
        return True

    def mark_complete(self):
        self.write({"is_completed": True})
        self.mapped("enrollment_id")._update_completion()
        return True

    def record_time(self, minutes):
        for record in self:
            record.time_spent += minutes
        self.mapped("enrollment_id")._recompute_time_spent()
        return True
