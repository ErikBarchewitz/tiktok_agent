# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GwoCourse(models.Model):
    _name = 'gwo.course'
    _description = 'GWO Training Course'
    _inherits = {'slide.channel': 'channel_id'}

    channel_id = fields.Many2one('slide.channel', required=True, ondelete='cascade', string='Learning Channel')
    gwo_domain = fields.Selection([
        ('onshore', 'Onshore'),
        ('offshore', 'Offshore'),
    ], default='onshore', required=True, string='GWO Domain')
    category = fields.Selection([
        ('refresher', 'Refresher'),
        ('initial', 'Initial'),
    ], default='refresher', required=True)
    validity_months = fields.Integer(default=24, string='Certificate Validity (months)')
    passing_score = fields.Float(default=80.0, string='Passing Score (%)')
    final_exam_id = fields.Many2one('survey.survey', string='Final Exam Survey', help='Final certification assessment.')
    total_duration_min = fields.Integer(compute='_compute_total_duration', store=True)
    certificate_template_id = fields.Many2one(
        'ir.actions.report',
        string='Certificate Report',
        domain="[('model', '=', 'gwo.enrollment')]",
    )
    content_ids = fields.One2many('gwo.content', 'course_id', string='Course Contents')
    enrollment_ids = fields.One2many('gwo.enrollment', 'course_id', string='Enrollments')
    instructor_ids = fields.Many2many('res.users', 'gwo_course_instructor_rel', 'course_id', 'user_id', string='Instructors')
    manager_id = fields.Many2one('res.users', string='Course Manager', default=lambda self: self.env.user)
    best_pass_rate = fields.Float(compute='_compute_metrics', string='Pass Rate (%)')
    average_score = fields.Float(compute='_compute_metrics', string='Average Score (%)')
    mandatory_content_count = fields.Integer(compute='_compute_content_counts', string='Mandatory Items')
    completion_count = fields.Integer(compute='_compute_metrics', string='Completed Enrollments')

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            'name': _('Enrollments'),
            'type': 'ir.actions.act_window',
            'res_model': 'gwo.enrollment',
            'view_mode': 'tree,form',
            'domain': [('course_id', '=', self.id)],
            'context': {'default_course_id': self.id},
        }

    def action_view_results(self):
        self.ensure_one()
        return {
            'name': _('Learner Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'gwo.user.result',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('enrollment_id.course_id', '=', self.id)],
        }

    def action_launch_final_exam(self):
        self.ensure_one()
        if not self.final_exam_id:
            raise UserError(_('No final exam configured for this course.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Launch Final Exam'),
            'res_model': 'gwo.launch.exam.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_course_id': self.id,
                'default_final_exam_id': self.final_exam_id.id,
            },
        }

    @api.depends('content_ids.estimated_minutes')
    def _compute_total_duration(self):
        for course in self:
            course.total_duration_min = sum(course.content_ids.mapped('estimated_minutes'))

    @api.depends('enrollment_ids.final_exam_score', 'enrollment_ids.passed')
    def _compute_metrics(self):
        for course in self:
            enrollments = course.enrollment_ids
            completed = enrollments.filtered(lambda e: e.final_exam_score)
            passed = enrollments.filtered(lambda e: e.passed)
            course.completion_count = len(completed)
            course.best_pass_rate = (len(passed) / len(enrollments) * 100.0) if enrollments else 0.0
            if completed:
                course.average_score = sum(completed.mapped('final_exam_score')) / len(completed)
            else:
                course.average_score = 0.0

    @api.depends('content_ids.is_mandatory')
    def _compute_content_counts(self):
        for course in self:
            course.mandatory_content_count = len(course.content_ids.filtered('is_mandatory'))

    def compute_progress(self, user):
        self.ensure_one()
        enrollment = self.enrollment_ids.filtered(lambda e: e.user_id == user)
        if enrollment:
            enrollment._compute_progress_pct()
        return enrollment.progress_pct if enrollment else 0.0

    def action_mark_slide_done(self, user, slide):
        self.ensure_one()
        content = self.content_ids.filtered(lambda c: c.slide_id == slide)
        if not content:
            return False
        enrollment = self.enrollment_ids.filtered(lambda e: e.user_id == user)
        if not enrollment:
            return False
        result = self.env['gwo.user.result'].search([
            ('enrollment_id', '=', enrollment.id),
            ('content_id', '=', content.id),
        ], limit=1)
        if not result:
            result = self.env['gwo.user.result'].create({
                'enrollment_id': enrollment.id,
                'content_id': content.id,
            })
        result.write({
            'status': 'done',
            'score': result.score or 0.0,
        })
        enrollment._compute_progress_pct()
        enrollment.write({'last_activity': fields.Datetime.now()})
        return True

    def _cron_update_progress(self):
        # Placeholder for scheduled recalculation hooks.
        for course in self.search([]):
            for enrollment in course.enrollment_ids:
                enrollment._compute_progress_pct()
