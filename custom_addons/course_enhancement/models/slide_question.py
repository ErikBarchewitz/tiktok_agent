from odoo import models, fields


class SlideQuestion(models.Model):
    _inherit = "slide.question"

    survey_question_id = fields.Many2one(
        "survey.question",
        string="Umfragefrage",
        ondelete="set null",
        help="Referenz zur ursprünglichen Survey-Frage für Synchronisierungen.",
    )


class SlideAnswer(models.Model):
    _inherit = "slide.answer"

    survey_answer_id = fields.Many2one(
        "survey.question.answer",
        string="Umfrageantwort",
        ondelete="set null",
        help="Referenz zur ursprünglichen Survey-Antwort für Synchronisierungen.",
    )
