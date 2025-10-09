# -*- coding: utf-8 -*-
"""Course section model."""

from odoo import fields, models


class AcademyCourseSection(models.Model):
    """Logical grouping of content inside a course."""

    _name = "academy.course.section"
    _description = "Course Section"
    _order = "sequence, id"

    name = fields.Char(required=True)
    channel_id = fields.Many2one(
        "slide.channel",
        string="Course",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    description = fields.Html()
    estimated_duration = fields.Float(
        string="Estimated Duration (minutes)", default=0.0
    )
    content_ids = fields.One2many(
        "academy.course.content",
        "section_id",
        string="Content",
    )
    color = fields.Integer(default=0)

    def name_get(self):
        return [(section.id, "%s - %s" % (section.channel_id.name, section.name)) for section in self]
