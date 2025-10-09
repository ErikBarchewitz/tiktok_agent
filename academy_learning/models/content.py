# -*- coding: utf-8 -*-
"""Course content model mapping to slides."""

from odoo import api, fields, models


class AcademyCourseContent(models.Model):
    """Wrap website slides to include extra metadata for the player."""

    _name = "academy.course.content"
    _description = "Course Content"
    _inherits = {"slide.slide": "slide_id"}
    _order = "sequence, id"

    slide_id = fields.Many2one("slide.slide", required=True, ondelete="cascade")
    section_id = fields.Many2one(
        "academy.course.section",
        required=True,
        ondelete="cascade",
        string="Section",
    )
    sequence = fields.Integer(default=10)
    content_kind = fields.Selection(
        selection=[
            ("markdown", "Article"),
            ("video", "Video"),
            ("image", "Image"),
            ("file", "Document"),
            ("quiz", "Quiz"),
            ("survey", "Survey"),
        ],
        required=True,
        default="markdown",
    )
    quiz_id = fields.Many2one("academy.quiz", string="Quiz")
    survey_id = fields.Many2one("survey.survey", string="Survey")
    allow_download = fields.Boolean(default=False)
    player_message = fields.Html(
        string="Learner Message",
        help="Optional helper text shown alongside the content.",
    )

    def open_content(self):
        """Return the proper frontend URL for the player."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/academy/content/%s" % self.id,
        }

    @api.onchange("content_kind")
    def _onchange_content_kind(self):
        if self.content_kind != "quiz":
            self.quiz_id = False
        if self.content_kind != "survey":
            self.survey_id = False
