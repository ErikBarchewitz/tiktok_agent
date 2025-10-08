# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    gwo_enrollment_id = fields.Many2one('gwo.enrollment', string='GWO Enrollment')

    def write(self, vals):
        previous_states = {record.id: record.state for record in self}
        res = super().write(vals)
        for record in self:
            state_before = previous_states.get(record.id)
            if record.state == 'done' and state_before != 'done':
                record._gwo_sync_results()
        return res

    def _gwo_sync_results(self):
        self.ensure_one()
        enrollment = self.gwo_enrollment_id
        if not enrollment:
            enrollment = self.env['gwo.enrollment'].search([
                ('user_id', '=', self.user_id.id if self.user_id else False),
                ('course_id.final_exam_id', '=', self.survey_id.id),
            ], limit=1)
        if not enrollment:
            return
        if enrollment.course_id.final_exam_id == self.survey_id:
            enrollment.mark_final_score(self.quizz_score)
            if enrollment.course_id.certificate_template_id:
                enrollment.course_id.certificate_template_id._render_qweb_pdf(enrollment.ids)
            return
        content = self.env['gwo.content'].search([
            ('course_id', '=', enrollment.course_id.id),
            ('related_quiz_id', '=', self.survey_id.id),
        ], limit=1)
        if not content:
            return
        result = self.env['gwo.user.result'].search([
            ('enrollment_id', '=', enrollment.id),
            ('content_id', '=', content.id),
        ], limit=1)
        if not result:
            result = self.env['gwo.user.result'].create({
                'enrollment_id': enrollment.id,
                'content_id': content.id,
            })
        result.mark_from_survey(self)


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    @api.depends('answer_score')
    def _compute_gwo_problematic(self):
        for line in self:
            line.gwo_is_problematic = line.answer_score < 1

    gwo_is_problematic = fields.Boolean(compute='_compute_gwo_problematic', string='Flagged in GWO Reports')
