# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CourseContent(models.Model):
    _name = "course.content"
    _description = "Course Content"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    course_id = fields.Many2one(
        "course.course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    content_type = fields.Selection(
        [
            ("video", "Video"),
            ("document", "Dokument"),
            ("quiz", "Reflexion"),
            ("template", "Template"),
            ("url", "Link"),
        ],
        required=True,
        default="document",
        tracking=True,
    )
    description = fields.Html()
    duration = fields.Integer(
        help="Estimated duration in minutes for the participant to complete this item.",
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Asset",
        help="Optionally upload a supporting file for this content entry.",
    )
    resource_url = fields.Char(string="External Resource")
    template_id = fields.Many2one(
        "course.content.template",
        string="Template",
        domain="[('content_type', '=', content_type)]",
    )
    is_template_based = fields.Boolean(
        compute="_compute_is_template_based",
        store=True,
    )
    active = fields.Boolean(default=True)

    @api.depends("template_id")
    def _compute_is_template_based(self):
        for content in self:
            content.is_template_based = bool(content.template_id)

    @api.onchange("template_id")
    def _onchange_template_id(self):
        for record in self:
            if record.template_id:
                template = record.template_id
                if template.description and not record.description:
                    record.description = template.description
                if template.default_duration and not record.duration:
                    record.duration = template.default_duration
                if template.attachment_id and not record.attachment_id:
                    record.attachment_id = template.attachment_id
                if template.resource_url and not record.resource_url:
                    record.resource_url = template.resource_url


class CourseContentTemplate(models.Model):
    _name = "course.content.template"
    _description = "Content Template"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    content_type = fields.Selection(
        [
            ("video", "Video"),
            ("document", "Dokument"),
            ("quiz", "Reflexion"),
            ("template", "Template"),
            ("url", "Link"),
        ],
        required=True,
        default="document",
    )
    description = fields.Html()
    default_duration = fields.Integer(
        help="Suggested duration (in minutes) when using this template."
    )
    attachment_id = fields.Many2one("ir.attachment", string="Asset")
    resource_url = fields.Char()
    tag_ids = fields.Many2many(
        "course.course.tag",
        string="Suggested Tags",
        help="Tags that work well with this template.",
    )
    is_recommended = fields.Boolean(default=False)

    _sql_constraints = [
        ("course_content_template_name_unique", "unique(name)", "Template names must be unique."),
    ]
