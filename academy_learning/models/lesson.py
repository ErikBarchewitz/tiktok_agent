# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AcademyLesson(models.Model):
    _name = "academy.lesson"
    _description = "Academy Learning Lesson"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    course_id = fields.Many2one("academy.course", required=True, ondelete="cascade")
    content = fields.Html(string="Inhalt", sanitize=True)
    duration_minutes = fields.Integer(string="Dauer (Minuten)")
    resource_url = fields.Char(string="Ressourcenlink")
    attachment_ids = fields.Many2many("ir.attachment", string="Anhänge")
    quiz_ids = fields.Many2many(
        "academy.quiz",
        "academy_lesson_quiz_rel",
        "lesson_id",
        "quiz_id",
        string="Zugeordnete Quizze",
    )

    @api.onchange("course_id")
    def _onchange_course(self):
        if self.course_id and not self.name:
            self.name = f"Lektion {len(self.course_id.lesson_ids) + 1}"
