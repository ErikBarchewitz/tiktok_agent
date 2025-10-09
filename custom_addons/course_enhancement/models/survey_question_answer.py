from odoo import api, models


class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    @api.model_create_multi
    def create(self, vals_list):
        answers = super().create(vals_list)
        answers._apply_elearning_binary_scores()
        return answers

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("binary_scoring_skip"):
            self._apply_elearning_binary_scores()
        return res

    def _apply_elearning_binary_scores(self):
        for answer in self:
            question = answer.question_id or answer.matrix_question_id
            if not question or not question.survey_id.is_elearning_quiz:
                continue
            desired_score = 1.0 if answer.is_correct else 0.0
            if answer.answer_score != desired_score:
                super(SurveyQuestionAnswer, answer.with_context(binary_scoring_skip=True)).write(
                    {"answer_score": desired_score}
                )
