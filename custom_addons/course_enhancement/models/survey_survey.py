from odoo import api, fields, models


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    is_elearning_quiz = fields.Boolean(
        string="Für eLearning verwenden",
        help="Aktivieren, um diese Umfrage mit eLearning-Inhalten zu synchronisieren."
             " Gamification wird deaktiviert und Fragen werden binär bewertet.",
    )
    slide_ids = fields.One2many(
        "slide.slide",
        "survey_id",
        string="Verknüpfte Folien",
    )

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._prepare_elearning_defaults(vals) for vals in vals_list]
        surveys = super().create(vals_list)
        surveys._apply_elearning_binary_constraints()
        return surveys

    def write(self, vals):
        res = super().write(self._prepare_elearning_defaults(vals))
        if not self.env.context.get("binary_scoring_skip"):
            self._apply_elearning_binary_constraints()
        return res

    def _prepare_elearning_defaults(self, vals):
        vals = dict(vals)
        if vals.get("is_elearning_quiz"):
            vals.setdefault("survey_type", "assessment")
            vals.setdefault("questions_layout", "page_per_question")
            vals.setdefault("questions_selection", "all")
            vals.setdefault("scoring_type", "scoring_with_answers")
        return vals

    def _apply_elearning_binary_constraints(self):
        for survey in self:
            if not survey.is_elearning_quiz:
                continue
            updates = {}
            if survey.survey_type != "assessment":
                updates["survey_type"] = "assessment"
            if survey.questions_layout != "page_per_question":
                updates["questions_layout"] = "page_per_question"
            if survey.questions_selection != "all":
                updates["questions_selection"] = "all"
            if survey.scoring_type != "scoring_with_answers":
                updates["scoring_type"] = "scoring_with_answers"
            if updates:
                super(SurveySurvey, survey.with_context(binary_scoring_skip=True)).write(updates)
            survey.question_ids._apply_elearning_binary_constraints()
