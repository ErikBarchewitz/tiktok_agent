# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GwoUserResult(models.Model):
    _name = 'gwo.user.result'
    _description = 'GWO Learner Result'
    _order = 'create_date desc'
    _sql_constraints = [
        ('unique_result_per_content', 'unique(enrollment_id, content_id)', 'Result already exists for this content.'),
    ]

    enrollment_id = fields.Many2one('gwo.enrollment', required=True, ondelete='cascade')
    content_id = fields.Many2one('gwo.content', required=True, ondelete='cascade')
    status = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='todo')
    score = fields.Float(default=0.0)
    survey_input_id = fields.Many2one('survey.user_input', string='Survey Attempt')

    @api.onchange('survey_input_id')
    def _onchange_survey_input_id(self):
        for record in self:
            if record.survey_input_id:
                record.score = record.survey_input_id.quizz_score
                if record.survey_input_id.state == 'done':
                    record.status = 'done'

    def mark_from_survey(self, survey_input):
        self.ensure_one()
        self.write({
            'survey_input_id': survey_input.id,
            'score': survey_input.quizz_score,
            'status': 'done' if survey_input.state == 'done' else self.status,
        })
        self.enrollment_id._compute_progress_pct()
        self.enrollment_id.write({'last_activity': fields.Datetime.now()})
