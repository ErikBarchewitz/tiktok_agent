# -*- coding: utf-8 -*-
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AcademyCourse(models.Model):
    _name = "academy.course"
    _description = "Academy Learning Course"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    tagline = fields.Char(help="Kurzer Claim, der im Frontend angezeigt wird.")
    description = fields.Html(string="Beschreibung", sanitize=True, tracking=True)
    token = fields.Char(
        string="Zugangs-Token",
        required=True,
        copy=False,
        default=lambda self: str(uuid.uuid4()),
        readonly=True,
    )
    access_url = fields.Char(string="Zugangslink", compute="_compute_access_url", store=True)
    lesson_ids = fields.One2many("academy.lesson", "course_id", string="Lektionen")
    quiz_ids = fields.One2many("academy.quiz", "course_id", string="Quizze")
    enrollment_ids = fields.One2many("academy.enrollment", "course_id", string="Einschreibungen")
    lesson_count = fields.Integer(compute="_compute_statistics", store=True)
    quiz_count = fields.Integer(compute="_compute_statistics", store=True)
    enrollment_count = fields.Integer(compute="_compute_statistics", store=True)
    is_published = fields.Boolean(
        string="Veröffentlicht",
        help="Nur veröffentlichte Kurse sind über den Link verfügbar.",
        default=False,
    )
    cover_image = fields.Binary(string="Titelbild")
    color = fields.Integer(default=0)

    _sql_constraints = [
        ("academy_course_token_unique", "unique(token)", "Der Zugangs-Token muss eindeutig sein."),
    ]

    def name_get(self):
        return [(record.id, f"{record.name}") for record in self]

    @api.depends("token")
    def _compute_access_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for course in self:
            if course.token:
                course.access_url = f"{base_url}/academy/{course.token}"
            else:
                course.access_url = False

    @api.depends("lesson_ids", "quiz_ids", "enrollment_ids")
    def _compute_statistics(self):
        for course in self:
            course.lesson_count = len(course.lesson_ids)
            course.quiz_count = len(course.quiz_ids)
            course.enrollment_count = len(course.enrollment_ids)

    def action_generate_new_token(self):
        for course in self:
            course.token = str(uuid.uuid4())
        return True

    def action_open_enrollments(self):
        self.ensure_one()
        return {
            "name": _("Einschreibungen"),
            "type": "ir.actions.act_window",
            "res_model": "academy.enrollment",
            "view_mode": "list,form",
            "domain": [["course_id", "=", self.id]],
        }

    def action_open_lessons(self):
        self.ensure_one()
        return {
            "name": _("Lektionen"),
            "type": "ir.actions.act_window",
            "res_model": "academy.lesson",
            "view_mode": "list,form",
            "domain": [["course_id", "=", self.id]],
        }

    def action_open_quizzes(self):
        self.ensure_one()
        return {
            "name": _("Quizze"),
            "type": "ir.actions.act_window",
            "res_model": "academy.quiz",
            "view_mode": "list,form",
            "domain": [["course_id", "=", self.id]],
        }

    def action_open_upload_wizard(self):
        self.ensure_one()
        return {
            "name": _("Kursinhalt hochladen"),
            "type": "ir.actions.act_window",
            "res_model": "academy.course.upload.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_course_id": self.id,
            },
        }

    @api.constrains("is_published", "lesson_ids")
    def _check_publishable(self):
        for course in self:
            if course.is_published and not course.lesson_ids:
                raise ValidationError(
                    _("Ein Kurs muss mindestens eine Lektion besitzen, bevor er veröffentlicht werden kann."))
