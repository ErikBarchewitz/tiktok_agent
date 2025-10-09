from odoo import api, fields, models


class SlideSlide(models.Model):
    _inherit = "slide.slide"

    template_id = fields.Many2one(
        "slide.content.template",
        string="Content Template",
        help="Template used to pre-fill structured learning content.",
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
        record = super().create(vals)
        template = record.template_id
        if template:
            record._apply_template(template)
        return record

    def write(self, vals):
        res = super().write(vals)
        if "template_id" in vals:
            for slide in self:
                if slide.template_id:
                    slide._apply_template(slide.template_id)
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
