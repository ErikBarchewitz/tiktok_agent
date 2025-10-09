# -*- coding: utf-8 -*-
"""Quiz entities for short formative assessments."""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AcademyQuiz(models.Model):
    _name = "academy.quiz"
    _description = "Academy Quiz"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Html()
    question_ids = fields.One2many("academy.quiz.question", "quiz_id", string="Questions")
    passing_score = fields.Float(default=0.0)
    show_feedback = fields.Boolean(default=True)
    attempt_ids = fields.One2many("academy.quiz.attempt", "quiz_id", string="Attempts")
    question_count = fields.Integer(compute="_compute_counts")
    average_score = fields.Float(compute="_compute_counts")

    def _compute_counts(self):
        for quiz in self:
            quiz.question_count = len(quiz.question_ids)
            if quiz.attempt_ids:
                quiz.average_score = sum(quiz.attempt_ids.mapped("score")) / len(quiz.attempt_ids)
            else:
                quiz.average_score = 0.0

    def action_open_attempts(self):
        self.ensure_one()
        action = self.env.ref("academy_learning.academy_quiz_attempt_action").read()[0]
        action["domain"] = [("quiz_id", "=", self.id)]
        return action

    def validate_manifest_dict(self, quiz_dict):
        """Used by the import wizard to validate quiz structures."""
        required = {"name", "questions"}
        if not required.issubset(quiz_dict):
            missing = required - quiz_dict.keys()
            raise ValidationError(_("Quiz manifest missing keys: %s") % ", ".join(sorted(missing)))
        for question in quiz_dict.get("questions", []):
            question_type = question.get("question_type")
            if question_type not in dict(self.env["academy.quiz.question"]._fields["question_type"].selection):
                raise ValidationError(_("Unsupported question type: %s") % question_type)
        return True


class AcademyQuizQuestion(models.Model):
    _name = "academy.quiz.question"
    _description = "Quiz Question"
    _order = "sequence, id"

    quiz_id = fields.Many2one("academy.quiz", required=True, ondelete="cascade")
    name = fields.Char(string="Prompt", required=True)
    sequence = fields.Integer(default=10)
    question_type = fields.Selection(
        [
            ("single", "Single Choice"),
            ("multiple", "Multiple Choice"),
            ("boolean", "True/False"),
            ("text", "Short Text"),
        ],
        default="single",
        required=True,
    )
    option_ids = fields.One2many("academy.quiz.answer", "question_id", string="Options")
    feedback_correct = fields.Text(string="Feedback (Correct)")
    feedback_incorrect = fields.Text(string="Feedback (Incorrect)")
    score = fields.Float(default=1.0)

    def _validate_option_integrity(self):
        for question in self:
            if question.question_type in ("single", "multiple"):
                correct_options = question.option_ids.filtered("is_correct")
                if not correct_options:
                    raise ValidationError(
                        _("Question '%s' requires at least one correct option.") % question.name
                    )
                if question.question_type == "single" and len(correct_options) != 1:
                    raise ValidationError(
                        _("Question '%s' must have exactly one correct option.") % question.name
                    )
            elif question.question_type == "boolean":
                if len(question.option_ids) != 2:
                    raise ValidationError(
                        _("Question '%s' should have exactly two options for True/False.") % question.name
                    )

    @api.constrains("question_type", "option_ids")
    def _check_options(self):
        self._validate_option_integrity()

    def export_to_dict(self):
        self.ensure_one()
        return {
            "name": self.name,
            "question_type": self.question_type,
            "sequence": self.sequence,
            "options": [option.export_to_dict() for option in self.option_ids],
            "score": self.score,
            "feedback_correct": self.feedback_correct,
            "feedback_incorrect": self.feedback_incorrect,
        }


class AcademyQuizAnswer(models.Model):
    _name = "academy.quiz.answer"
    _description = "Quiz Answer Option"
    _order = "sequence, id"

    question_id = fields.Many2one("academy.quiz.question", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    is_correct = fields.Boolean(default=False)
    sequence = fields.Integer(default=10)
    value = fields.Char(help="Optional identifier used during imports/exports.")

    def export_to_dict(self):
        self.ensure_one()
        return {
            "name": self.name,
            "is_correct": self.is_correct,
            "sequence": self.sequence,
            "value": self.value,
        }


class AcademyQuizAttempt(models.Model):
    _name = "academy.quiz.attempt"
    _description = "Quiz Attempt"
    _order = "create_date desc"

    quiz_id = fields.Many2one("academy.quiz", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True)
    enrollment_id = fields.Many2one("academy.course.enrollment", string="Enrollment")
    question_line_ids = fields.One2many(
        "academy.quiz.attempt.line", "attempt_id", string="Question Lines"
    )
    score = fields.Float(readonly=True)
    max_score = fields.Float(readonly=True)
    passed = fields.Boolean(readonly=True)
    time_spent = fields.Float(string="Time Spent (minutes)", default=0.0)

    def _score_attempt(self):
        for attempt in self:
            score = 0.0
            max_score = 0.0
            for line in attempt.question_line_ids:
                max_score += line.question_id.score
                if line.is_correct:
                    score += line.question_id.score
            attempt.score = score
            attempt.max_score = max_score
            attempt.passed = score >= attempt.quiz_id.passing_score

    @api.model_create_multi
    def create(self, vals_list):
        attempts = super().create(vals_list)
        attempts._score_attempt()
        if attempts.mapped("enrollment_id"):
            attempts.mapped("enrollment_id")._update_progress_from_attempts(attempts)
        return attempts

    def export_to_dict(self):
        self.ensure_one()
        return {
            "quiz": self.quiz_id.name,
            "score": self.score,
            "max_score": self.max_score,
            "passed": self.passed,
            "answers": [line.export_to_dict() for line in self.question_line_ids],
        }


class AcademyQuizAttemptLine(models.Model):
    _name = "academy.quiz.attempt.line"
    _description = "Quiz Attempt Question Line"

    attempt_id = fields.Many2one("academy.quiz.attempt", required=True, ondelete="cascade")
    question_id = fields.Many2one("academy.quiz.question", required=True)
    selected_option_ids = fields.Many2many("academy.quiz.answer", string="Selected Options")
    free_text_value = fields.Char()
    is_correct = fields.Boolean(default=False)

    @api.onchange("selected_option_ids", "free_text_value")
    def _onchange_values(self):
        for line in self:
            if line.question_id.question_type in ("single", "multiple", "boolean"):
                expected = set(line.question_id.option_ids.filtered("is_correct").ids)
                actual = set(line.selected_option_ids.ids)
                line.is_correct = expected == actual
            elif line.question_id.question_type == "text":
                line.is_correct = bool(line.free_text_value)

    def export_to_dict(self):
        self.ensure_one()
        return {
            "question": self.question_id.name,
            "selected": self.selected_option_ids.mapped("name"),
            "free_text": self.free_text_value,
            "is_correct": self.is_correct,
        }
