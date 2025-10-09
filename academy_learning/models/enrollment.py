# -*- coding: utf-8 -*-
"""Enrollment model to track learner progress."""

from odoo import api, fields, models


class AcademyCourseEnrollment(models.Model):
    _name = "academy.course.enrollment"
    _description = "Course Enrollment"
    _order = "create_date desc"

    channel_id = fields.Many2one("slide.channel", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True)
    state = fields.Selection(
        [
            ("active", "Active"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
    )
    progress_line_ids = fields.One2many(
        "academy.course.progress", "enrollment_id", string="Progress Lines"
    )
    completion_ratio = fields.Float(default=0.0, readonly=True)
    completed_on = fields.Datetime(readonly=True)
    time_spent = fields.Float(string="Time Spent (minutes)", default=0.0)
    quiz_attempt_ids = fields.One2many("academy.quiz.attempt", "enrollment_id")

    _sql_constraints = [
        ("academy_unique_enrollment", "unique(channel_id, user_id)", "The user is already enrolled."),
    ]

    def _update_completion(self):
        for enrollment in self:
            total = len(enrollment.progress_line_ids)
            completed = len(enrollment.progress_line_ids.filtered(lambda l: l.is_completed))
            enrollment.completion_ratio = completed / total if total else 0.0
            if enrollment.completion_ratio >= 1 and enrollment.state != "completed":
                enrollment.state = "completed"
                enrollment.completed_on = fields.Datetime.now()

    def _update_progress_from_attempts(self, attempts):
        for enrollment in self:
            lines = enrollment.progress_line_ids.filtered(
                lambda l: l.content_id.content_kind == "quiz" and l.content_id.quiz_id in attempts.mapped("quiz_id")
            )
            for line in lines:
                relevant_attempts = attempts.filtered(lambda a: a.quiz_id == line.content_id.quiz_id)
                if relevant_attempts:
                    line.latest_score = max(relevant_attempts.mapped("score"))
                    line.is_completed = any(a.passed for a in relevant_attempts)
            enrollment._update_completion()

    def action_reset_progress(self):
        self.progress_line_ids.write({"is_completed": False, "latest_score": 0.0})
        self.write({"completion_ratio": 0.0, "state": "active", "completed_on": False})

    def _recompute_time_spent(self):
        for enrollment in self:
            quiz_minutes = sum(enrollment.quiz_attempt_ids.mapped("time_spent"))
            study_minutes = sum(enrollment.progress_line_ids.mapped("time_spent"))
            enrollment.time_spent = quiz_minutes + study_minutes

    def ensure_progress_lines(self):
        for enrollment in self:
            missing_content = enrollment.channel_id.academy_section_ids.mapped("content_ids") - enrollment.progress_line_ids.mapped("content_id")
            for content in missing_content:
                self.env["academy.course.progress"].create(
                    {
                        "enrollment_id": enrollment.id,
                        "content_id": content.id,
                    }
                )
            enrollment._update_completion()

    @api.model
    def create(self, vals):
        enrollment = super().create(vals)
        enrollment.ensure_progress_lines()
        return enrollment
