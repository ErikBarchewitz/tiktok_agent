# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AcademyQuiz(models.Model):
    _name = "academy.quiz"
    _description = "Academy Learning Quiz"
    _order = "sequence, id"

    name = fields.Char(required=True)
    course_id = fields.Many2one("academy.course", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    introduction = fields.Html(string="Einleitung", sanitize=True)
    question_ids = fields.One2many("academy.quiz.question", "quiz_id", string="Fragen")
    passing_score = fields.Integer(
        string="Bestehensgrenze",
        default=60,
        help="Prozentualer Wert, der für das Bestehen des Quiz erreicht werden muss.",
    )
    attempts_allowed = fields.Integer(string="Versuche erlaubt", default=0, help="0 bedeutet unbegrenzt")

    @api.constrains("passing_score")
    def _check_passing_score(self):
        for quiz in self:
            if quiz.passing_score < 0 or quiz.passing_score > 100:
                raise ValidationError(_("Die Bestehensgrenze muss zwischen 0 und 100 liegen."))


class AcademyQuizQuestion(models.Model):
    _name = "academy.quiz.question"
    _description = "Academy Learning Quiz Question"
    _order = "sequence, id"

    name = fields.Char(string="Frage", required=True)
    sequence = fields.Integer(default=10)
    quiz_id = fields.Many2one("academy.quiz", required=True, ondelete="cascade")
    question_type = fields.Selection(
        [
            ("single", "Single Choice"),
            ("multiple", "Multiple Choice"),
            ("text", "Freitext"),
        ],
        default="single",
        required=True,
    )
    answer_ids = fields.One2many("academy.quiz.answer", "question_id", string="Antworten")
    explanation = fields.Text(string="Erklärung")

    def correct_answer_ids(self):
        return self.answer_ids.filtered("is_correct")


class AcademyQuizAnswer(models.Model):
    _name = "academy.quiz.answer"
    _description = "Academy Learning Quiz Answer"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    question_id = fields.Many2one("academy.quiz.question", required=True, ondelete="cascade")
    is_correct = fields.Boolean(default=False)
