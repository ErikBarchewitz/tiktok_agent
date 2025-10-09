# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CourseCourse(models.Model):
    """High level course configuration with manual attendee management."""

    _name = "course.course"
    _description = "Course"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    description = fields.Html()
    responsible_id = fields.Many2one(
        "res.users",
        string="Course Owner",
        default=lambda self: self.env.user,
        tracking=True,
    )
    content_ids = fields.One2many("course.content", "course_id", string="Contents")
    attendee_ids = fields.One2many("course.attendee", "course_id", string="Attendees")
    active = fields.Boolean(default=True)
    total_content = fields.Integer(
        compute="_compute_metrics", store=True, string="Content Items"
    )
    total_attendees = fields.Integer(
        compute="_compute_metrics", store=True, string="Attendees"
    )
    avg_progress = fields.Float(
        compute="_compute_avg_progress",
        string="Average Progress",
        digits=(16, 2),
        help="Average of the completion percentage of all attendees.",
    )
    allow_template_upload = fields.Boolean(
        string="Enable Curated Templates",
        default=True,
        help="If enabled, facilitators can reuse curated templates when creating new content.",
    )

    tag_ids = fields.Many2many(
        'course.course.tag',
        'course_course_tag_rel',
        'course_id',
        'tag_id',
        string='Tags',
        help='Organise courses with thematic tags.',
    )

    _sql_constraints = [
        ("course_code_unique", "unique(code)", "The course code must be unique."),
    ]

    @api.depends("content_ids", "content_ids.active")
    def _compute_metrics(self):
        for course in self:
            contents = course.content_ids.filtered(lambda c: c.active)
            course.total_content = len(contents)
            course.total_attendees = len(course.attendee_ids)

    @api.depends("attendee_ids.progress")
    def _compute_avg_progress(self):
        for course in self:
            if course.attendee_ids:
                course.avg_progress = sum(course.attendee_ids.mapped("progress")) / len(
                    course.attendee_ids
                )
            else:
                course.avg_progress = 0.0

    def action_view_contents(self):
        self.ensure_one()
        action = self.env.ref("course_hub.action_course_content").read()[0]
        action["domain"] = [("course_id", "=", self.id)]
        action["context"] = {
            "default_course_id": self.id,
            "default_allow_template_upload": self.allow_template_upload,
        }
        return action

    def action_view_attendees(self):
        self.ensure_one()
        action = self.env.ref("course_hub.action_course_attendee").read()[0]
        action["domain"] = [("course_id", "=", self.id)]
        action["context"] = {"default_course_id": self.id}
        return action

    def action_toggle_templates(self):
        for course in self:
            course.allow_template_upload = not course.allow_template_upload


class CourseCourseTag(models.Model):
    _name = "course.course.tag"
    _description = "Course Tag"

    name = fields.Char(required=True)
    color = fields.Integer(default=0)
    course_ids = fields.Many2many(
        'course.course',
        'course_course_tag_rel',
        'tag_id',
        'course_id',
        string='Courses',
    )

    _sql_constraints = [
        ("course_tag_name_unique", "unique(name)", "The tag name must be unique."),
    ]
