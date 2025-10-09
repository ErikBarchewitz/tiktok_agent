# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models


class AcademyEnrollment(models.Model):
    _name = "academy.enrollment"
    _description = "Academy Learning Enrollment"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    course_id = fields.Many2one("academy.course", required=True, ondelete="cascade", tracking=True)
    partner_id = fields.Many2one("res.partner", required=True, tracking=True)
    email = fields.Char(related="partner_id.email", store=True)
    progress = fields.Float(default=0.0, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Neu"),
            ("in_progress", "In Bearbeitung"),
            ("done", "Abgeschlossen"),
        ],
        default="draft",
        tracking=True,
    )
    quiz_score = fields.Float(string="Letzte Quizbewertung")
    completed_at = fields.Datetime(string="Abgeschlossen am")
    access_token = fields.Char(string="Zugangs-Token", copy=False)
    submission_ids = fields.One2many("academy.quiz.submission", "enrollment_id", string="Quizteilnahmen")
    lesson_progress_ids = fields.One2many("academy.lesson.progress", "enrollment_id", string="Lektionen")

    _sql_constraints = [
        (
            "academy_enrollment_unique",
            "unique(course_id, partner_id)",
            "Der Teilnehmer ist bereits für diesen Kurs eingeschrieben.",
        )
    ]

    @api.depends("partner_id", "course_id")
    def _compute_name(self):
        for enrollment in self:
            if enrollment.partner_id and enrollment.course_id:
                enrollment.name = f"{enrollment.partner_id.name} - {enrollment.course_id.name}"
            else:
                enrollment.name = False

    def action_mark_in_progress(self):
        self.write({"state": "in_progress"})

    def action_mark_done(self):
        self.write({"state": "done", "completed_at": datetime.utcnow()})

    def update_progress(self, value):
        for enrollment in self:
            enrollment.progress = max(0.0, min(100.0, value))
            if enrollment.progress >= 100.0:
                enrollment.state = "done"
                enrollment.completed_at = datetime.utcnow()
            elif enrollment.progress > 0 and enrollment.state == "draft":
                enrollment.state = "in_progress"

    def recompute_progress(self):
        for enrollment in self:
            course = enrollment.course_id
            total_items = len(course.lesson_ids) + len(course.quiz_ids)
            completed_lessons = len(enrollment.lesson_progress_ids)
            passed_quizzes = len(enrollment.submission_ids.filtered("is_passed"))
            completion = 0.0
            if total_items:
                completion = (completed_lessons + passed_quizzes) / total_items * 100
            enrollment.update_progress(completion)


class AcademyQuizSubmission(models.Model):
    _name = "academy.quiz.submission"
    _description = "Academy Learning Quiz Submission"
    _order = "create_date desc"

    name = fields.Char(required=True)
    enrollment_id = fields.Many2one("academy.enrollment", required=True, ondelete="cascade")
    quiz_id = fields.Many2one("academy.quiz", required=True, ondelete="cascade")
    score = fields.Float(string="Ergebnis in %")
    is_passed = fields.Boolean(string="Bestanden")
    answer_json = fields.Text(string="Antworten (JSON)")


class AcademyLessonProgress(models.Model):
    _name = "academy.lesson.progress"
    _description = "Academy Learning Lesson Progress"
    _order = "completed_at desc"

    enrollment_id = fields.Many2one("academy.enrollment", required=True, ondelete="cascade")
    lesson_id = fields.Many2one("academy.lesson", required=True, ondelete="cascade")
    completed_at = fields.Datetime(default=lambda self: fields.Datetime.now())

    _sql_constraints = [
        ("academy_lesson_progress_unique", "unique(enrollment_id, lesson_id)", "Die Lektion wurde bereits abgeschlossen."),
    ]
