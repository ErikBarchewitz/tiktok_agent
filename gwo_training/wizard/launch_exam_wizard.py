# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GwoLaunchExamWizard(models.TransientModel):
    _name = 'gwo.launch.exam.wizard'
    _description = 'Launch Final Exam Wizard'

    course_id = fields.Many2one('gwo.course', required=True)
    enrollment_id = fields.Many2one('gwo.enrollment', string='Enrollment')
    final_exam_id = fields.Many2one('survey.survey', required=True)
    launch_mode = fields.Selection([
        ('in_app', 'In-Application'),
        ('external', 'External Link'),
    ], default='in_app')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not res.get('enrollment_id') and res.get('course_id'):
            enrollment = self.env['gwo.enrollment'].search([
                ('course_id', '=', res['course_id']),
                ('user_id', '=', self.env.user.id),
            ], limit=1)
            if enrollment:
                res['enrollment_id'] = enrollment.id
        return res

    def action_launch(self):
        self.ensure_one()
        if not self.final_exam_id:
            raise UserError(_('Please select a final exam.'))
        enrollment = self.enrollment_id
        if not enrollment:
            enrollment = self.env['gwo.enrollment'].create({
                'user_id': self.env.user.id,
                'course_id': self.course_id.id,
            })
            self.enrollment_id = enrollment
        survey = self.final_exam_id.sudo()
        user_input = survey._create_answer(
            partner=enrollment.user_id.partner_id,
            email=enrollment.user_id.email or enrollment.user_id.partner_id.email,
        )
        user_input.write({
            'state': 'in_progress',
            'gwo_enrollment_id': enrollment.id,
        })
        action = survey.action_start_survey()
        action.update({
            'context': {
                'survey_token': user_input.token,
                'lang': self.env.user.lang,
            }
        })
        return action
