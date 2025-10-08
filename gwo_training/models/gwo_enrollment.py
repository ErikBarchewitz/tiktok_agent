# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GwoEnrollment(models.Model):
    _name = 'gwo.enrollment'
    _description = 'GWO Enrollment'
    _sql_constraints = [
        ('gwo_enrollment_unique_user_course', 'unique(user_id, course_id)', 'A learner can only enroll once in a course.'),
    ]

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    course_id = fields.Many2one('gwo.course', required=True, ondelete='cascade')
    progress_pct = fields.Float(compute='_compute_progress_pct', store=True)
    passed = fields.Boolean(compute='_compute_passed', store=True)
    final_exam_score = fields.Float(default=0.0)
    last_activity = fields.Datetime(default=fields.Datetime.now)
    result_ids = fields.One2many('gwo.user.result', 'enrollment_id', string='Content Results')

    @api.depends('result_ids.status', 'course_id.content_ids.is_mandatory')
    def _compute_progress_pct(self):
        for enrollment in self:
            mandatory = enrollment.course_id.content_ids.filtered('is_mandatory')
            if not mandatory:
                enrollment.progress_pct = 0.0
                continue
            completed = enrollment.result_ids.filtered(lambda r: r.content_id in mandatory and r.status == 'done')
            enrollment.progress_pct = (len(completed) / len(mandatory)) * 100.0

    @api.depends('final_exam_score', 'course_id.passing_score')
    def _compute_passed(self):
        for enrollment in self:
            enrollment.passed = bool(enrollment.final_exam_score and enrollment.final_exam_score >= enrollment.course_id.passing_score)

    def action_launch_final_exam(self):
        self.ensure_one()
        return self.course_id.action_launch_final_exam()

    def mark_final_score(self, score):
        self.ensure_one()
        self.write({
            'final_exam_score': score,
            'last_activity': fields.Datetime.now(),
        })
