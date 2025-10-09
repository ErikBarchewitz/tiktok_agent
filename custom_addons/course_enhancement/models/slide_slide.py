from odoo import _, api, fields, models


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    template_id = fields.Many2one(
        "slide.content.template",
        string="Content Template",
        help="Template used to pre-fill structured learning content.",
    )
    survey_id = fields.Many2one(
        "survey.survey",
        string="Survey",
        ondelete="set null",
        help="Assessment linked to this quiz slide for binary scoring.",
        domain="[('survey_type', '=', 'assessment')]",
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
        if not vals.get("template_id") and vals.get("channel_id"):
            channel = self.env["slide.channel"].browse(vals["channel_id"])
            if channel and channel.default_template_id:
                vals.setdefault("template_id", channel.default_template_id.id)
        vals = self._prepare_quiz_survey_vals(vals)
        record = super().create(vals)
        template = record.template_id
        if template:
            record._apply_template(template)
        record._sync_quiz_survey_title()
        return record

    def write(self, vals):
        res = True
        for slide in self:
            update_vals = slide._prepare_quiz_survey_vals(dict(vals), current_slide=slide)
            res = super(SlideSlide, slide).write(update_vals) and res
            if "template_id" in update_vals and slide.template_id:
                slide._apply_template(slide.template_id)
            if any(field in vals for field in ["name", "survey_id", "slide_type"]):
                slide._sync_quiz_survey_title()
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

    def _prepare_quiz_survey_vals(self, vals, current_slide=None):
        """Ensure quiz slides always reference an assessment survey."""
        prepared_vals = dict(vals)
        slide_type = prepared_vals.get("slide_type") or (current_slide.slide_type if current_slide else False)
        if slide_type == "quiz":
            if not prepared_vals.get("survey_id"):
                if current_slide and current_slide.survey_id:
                    prepared_vals["survey_id"] = current_slide.survey_id.id
                else:
                    survey = self._create_binary_survey(prepared_vals, current_slide=current_slide)
                    prepared_vals["survey_id"] = survey.id
        elif "slide_type" in prepared_vals or (current_slide and current_slide.slide_type == "quiz"):
            prepared_vals.setdefault("survey_id", False)
        return prepared_vals

    def _create_binary_survey(self, vals, current_slide=None):
        title = vals.get("name")
        if not title and current_slide:
            title = current_slide.name
        if not title:
            title = _("Quiz")
        return self.env["survey.survey"].create(
            {
                "title": title,
                "survey_type": "assessment",
                "scoring_type": "scoring_with_answers",
            }
        )

    def _sync_quiz_survey_title(self):
        for slide in self.filtered(lambda s: s.slide_type == "quiz" and s.survey_id):
            if slide.name:
                slide.survey_id.sudo().write({"title": slide.name})
