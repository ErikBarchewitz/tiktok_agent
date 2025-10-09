from odoo import fields, models


class SlideContentTemplate(models.Model):
    _name = "slide.content.template"
    _description = "Slide Content Template"
    _order = "name"

    name = fields.Char(required=True)
    description = fields.Text()
    slide_type = fields.Selection(
        [
            ("document", "Dokument"),
            ("presentation", "Präsentation"),
            ("video", "Video"),
            ("quiz", "Quiz"),
        ],
        string="Content Type",
        default="document",
    )
    body_html = fields.Html(string="Rich Content")
    estimated_duration = fields.Integer(
        string="Estimated Duration (minutes)",
        help="Suggested duration for the learning unit.",
    )
    tag_ids = fields.Many2many(
        "slide.tag",
        "slide_content_template_tag_rel",
        "template_id",
        "tag_id",
        string="Suggested Tags",
    )
