# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GwoContent(models.Model):
    _name = 'gwo.content'
    _description = 'GWO Course Content'
    _inherits = {'slide.slide': 'slide_id'}
    _order = 'sequence, id'

    slide_id = fields.Many2one('slide.slide', required=True, ondelete='cascade')
    course_id = fields.Many2one('gwo.course', required=True, ondelete='cascade')
    content_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('presentation', 'Presentation'),
        ('link', 'External Link'),
        ('video', 'Video'),
        ('quiz', 'Quiz'),
    ], default='text', required=True)
    estimated_minutes = fields.Integer(default=5)
    is_mandatory = fields.Boolean(default=True)
    related_quiz_id = fields.Many2one('survey.survey', string='Related Quiz')

    @staticmethod
    def _update_slide_channel(records):
        for record in records:
            if record.course_id and record.slide_id.channel_id != record.course_id.channel_id:
                record.slide_id.channel_id = record.course_id.channel_id

    @staticmethod
    def _ensure_related_quiz(records):
        for record in records.filtered(lambda r: r.content_type == 'quiz' and not r.related_quiz_id):
            record.related_quiz_id = record.slide_id.survey_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._update_slide_channel(records)
        self._ensure_related_quiz(records)
        return records

    def write(self, vals):
        res = super().write(vals)
        self._update_slide_channel(self)
        self._ensure_related_quiz(self)
        return res

    def action_open_related_quiz(self):
        self.ensure_one()
        if self.related_quiz_id:
            return {
                'type': 'ir.actions.act_window',
                'name': self.related_quiz_id.title,
                'res_model': 'survey.survey',
                'res_id': self.related_quiz_id.id,
                'view_mode': 'form',
            }
        return False
