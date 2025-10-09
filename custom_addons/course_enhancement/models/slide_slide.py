from odoo import api, fields, models


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    template_id = fields.Many2one(
        "slide.content.template",
        string="Content Template",
        help="Template used to pre-fill structured learning content.",
    )
    survey_id = fields.Many2one(
        "survey.survey",
        string="Verknüpfte Umfrage",
        help="Quizfragen aus dieser Umfrage werden mit dem Inhalt synchronisiert.",
        domain="[('is_elearning_quiz', '=', True)]",
    )

    @api.onchange("channel_id")
    def _onchange_channel_default_template(self):
        if self.channel_id and self.channel_id.default_template_id:
            self.template_id = self.channel_id.default_template_id

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if self.template_id:
            template = self.template_id
            if template.name and not self.name:
                self.name = template.name
            if template.description:
                self.description = template.description
            if template.body_html:
                self.html_content = template.body_html
            if template.slide_type and (not self.slide_type or self.slide_type == "document"):
                self.slide_type = template.slide_type

    @api.model
    def create(self, vals):
        vals = self._apply_quiz_rewards_defaults(vals)
        if not vals.get("template_id") and vals.get("channel_id"):
            channel = self.env["slide.channel"].browse(vals["channel_id"])
            if channel and channel.default_template_id:
                vals.setdefault("template_id", channel.default_template_id.id)
        record = super().create(vals)
        template = record.template_id
        if template:
            record._apply_template(template)
        if record.survey_id:
            record._sync_survey_questions_from_survey()
        return record

    def write(self, vals):
        vals = self._apply_quiz_rewards_defaults(vals)
        res = super().write(vals)
        if "template_id" in vals:
            for slide in self:
                if slide.template_id:
                    slide._apply_template(slide.template_id)
        if "survey_id" in vals:
            for slide in self:
                slide._sync_survey_questions_from_survey()
        return res

    def _apply_template(self, template):
        update_vals = {}
        if template.name and not self.name:
            update_vals["name"] = template.name
        if template.description and not self.description:
            update_vals["description"] = template.description
        if template.body_html and not self.html_content:
            update_vals["html_content"] = template.body_html
        if template.slide_type and not self.slide_type:
            update_vals["slide_type"] = template.slide_type
        if update_vals:
            super(SlideSlide, self).write(update_vals)

    def _apply_quiz_rewards_defaults(self, vals):
        rewards_fields = [
            "quiz_first_attempt_reward",
            "quiz_second_attempt_reward",
            "quiz_third_attempt_reward",
            "quiz_fourth_attempt_reward",
        ]
        # Ensure rewards are neutralised when gamification is disabled.
        for field_name in rewards_fields:
            if field_name in self._fields:
                vals[field_name] = 0
        return vals

    def action_sync_survey_questions(self):
        self.ensure_one()
        self._sync_survey_questions_from_survey()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Umfrage synchronisiert",
                "message": "Die Fragen wurden aus der verknüpften Umfrage übernommen.",
                "sticky": False,
                "type": "success",
            },
        }

    def _sync_survey_questions_from_survey(self):
        for slide in self:
            if not slide.survey_id:
                continue
            survey_questions = slide.survey_id.question_ids.filtered(
                lambda q: not q.is_page and q.question_type in ("simple_choice", "multiple_choice")
            )
            sequence = 1
            for survey_question in survey_questions:
                answer_commands = [(5, 0, 0)]
                for suggested_answer in survey_question.suggested_answer_ids:
                    text_value = suggested_answer.value or suggested_answer.value_label or ""
                    answer_commands.append(
                        (
                            0,
                            0,
                            {
                                "text_value": text_value,
                                "is_correct": suggested_answer.is_correct,
                                "sequence": suggested_answer.sequence,
                                "survey_answer_id": suggested_answer.id,
                            },
                        )
                    )
                question_vals = {
                    "question": survey_question.title or "",
                    "sequence": sequence,
                    "survey_question_id": survey_question.id,
                    "answer_ids": answer_commands,
                }
                existing_question = slide.question_ids.filtered(
                    lambda q: q.survey_question_id == survey_question
                )[:1]
                if existing_question:
                    existing_question.write(question_vals)
                else:
                    question_vals.update({"slide_id": slide.id})
                    self.env["slide.question"].create(question_vals)
                sequence += 1
            # Remove orphan questions that are no longer present in the survey
            linked_ids = survey_questions.ids
            orphan_questions = slide.question_ids.filtered(
                lambda q: q.survey_question_id and q.survey_question_id.id not in linked_ids
            )
            if orphan_questions:
                orphan_questions.unlink()
