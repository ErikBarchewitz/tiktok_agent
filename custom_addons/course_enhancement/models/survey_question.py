from odoo import api, models


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    @api.model_create_multi
    def create(self, vals_list):
        questions = super().create(vals_list)
        questions._apply_elearning_binary_constraints()
        return questions

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("binary_scoring_skip"):
            self._apply_elearning_binary_constraints()
        return res

    def _apply_elearning_binary_constraints(self):
        for question in self:
            survey = question.survey_id
            if not survey or not survey.is_elearning_quiz:
                continue
            updates = {}
            if question.question_type not in ("simple_choice", "multiple_choice"):
                updates["question_type"] = "simple_choice"
            if question.is_scored_question is not True:
                updates["is_scored_question"] = True
            if updates:
                super(SurveyQuestion, question.with_context(binary_scoring_skip=True)).write(updates)
            question.suggested_answer_ids._apply_elearning_binary_scores()
