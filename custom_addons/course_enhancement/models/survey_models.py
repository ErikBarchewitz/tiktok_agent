from odoo import api, fields, models


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    def _disable_gamification_values(self, vals):
        disabled_fields = [
            "certification_give_badge",
            "certification_badge_id",
            "session_speed_rating",
        ]
        result = dict(vals)
        for field_name in disabled_fields:
            if field_name in self._fields:
                result[field_name] = False
        return result

    @api.model
    def create(self, vals):
        vals = self._disable_gamification_values(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._disable_gamification_values(vals)
        return super().write(vals)


class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    def _prepare_binary_score(self, vals):
        prepared_vals = dict(vals)
        if "is_correct" in prepared_vals:
            prepared_vals["answer_score"] = 1.0 if prepared_vals["is_correct"] else 0.0
        elif "answer_score" not in prepared_vals:
            is_correct = None
            if self:
                is_correct = self.is_correct
            if is_correct is not None:
                prepared_vals.setdefault("answer_score", 1.0 if is_correct else 0.0)
        return prepared_vals

    @api.model
    def create(self, vals):
        vals = self._prepare_binary_score(vals)
        return super().create(vals)

    def write(self, vals):
        res = True
        for answer in self:
            update_vals = answer._prepare_binary_score(dict(vals))
            res = super(SurveyQuestionAnswer, answer).write(update_vals) and res
        return res


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    def _compute_scoring_values(self):
        for user_input in self:
            questions = user_input.predefined_question_ids.filtered(self._question_supports_binary_scoring)
            total_questions = len(questions)
            if not total_questions:
                user_input.scoring_total = 0.0
                user_input.scoring_percentage = 0.0
                continue

            correct_count = sum(
                1 for question in questions if self._is_question_answer_correct(user_input, question)
            )
            user_input.scoring_total = float(correct_count)
            percentage = (correct_count / total_questions) * 100.0
            user_input.scoring_percentage = round(percentage, 2) if percentage else 0.0

    def _question_supports_binary_scoring(self, question):
        if question.question_type in ("simple_choice", "multiple_choice"):
            return bool(question.suggested_answer_ids.filtered("is_correct"))
        return question.is_scored_question

    def _is_question_answer_correct(self, user_input, question):
        if question.question_type == "multiple_choice":
            lines = user_input.user_input_line_ids.filtered(
                lambda line: line.question_id == question and not line.skipped and line.answer_type == "suggestion"
            )
            if not lines:
                return False
            selected_answer_ids = set(lines.mapped("suggested_answer_id").ids)
            correct_answer_ids = set(question.suggested_answer_ids.filtered("is_correct").ids)
            return selected_answer_ids == correct_answer_ids

        if question.question_type == "simple_choice":
            line = user_input.user_input_line_ids.filtered(
                lambda l: l.question_id == question and not l.skipped and l.answer_type == "suggestion"
            )
            return len(line) == 1 and all(line.mapped("answer_is_correct"))

        relevant_lines = user_input.user_input_line_ids.filtered(
            lambda line: line.question_id == question and not line.skipped
        )
        return any(relevant_lines.mapped("answer_is_correct"))

    def _multiple_choice_question_answer_result(self, user_input_lines, question_correct_suggested_answers):
        relevant_lines = user_input_lines.filtered(
            lambda line: not line.skipped and line.answer_type == "suggestion"
        )
        if not relevant_lines:
            return "skipped"
        selected_answer_ids = set(relevant_lines.mapped("suggested_answer_id").ids)
        correct_answer_ids = set(question_correct_suggested_answers.ids)
        return "correct" if selected_answer_ids == correct_answer_ids else "incorrect"

    def _simple_choice_question_answer_result(
        self, user_input_line, question_correct_suggested_answers, question_incorrect_scored_answers
    ):
        if user_input_line.skipped:
            return "skipped"
        if user_input_line.suggested_answer_id in question_correct_suggested_answers:
            return "correct"
        return "incorrect"


class SurveyUserInputLine(models.Model):
    _inherit = "survey.user_input.line"

    @api.model
    def _get_answer_score_values(self, vals, compute_speed_score=True):
        values = super()._get_answer_score_values(vals, compute_speed_score=False)
        values["answer_score"] = 1.0 if values.get("answer_is_correct") else 0.0
        return values
