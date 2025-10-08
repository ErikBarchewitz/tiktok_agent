# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class GwoTrainingPortal(http.Controller):

    @http.route('/gwo/course/<int:course_id>/final_exam/start', type='http', auth='user', website=True)
    def start_final_exam(self, course_id, **kwargs):
        course = request.env['gwo.course'].sudo().browse(course_id)
        if not course.exists() or not course.final_exam_id:
            return request.not_found()
        user = request.env.user
        enrollment = request.env['gwo.enrollment'].sudo().search([
            ('course_id', '=', course.id),
            ('user_id', '=', user.id),
        ], limit=1)
        if not enrollment:
            if user.has_group('gwo_training.group_gwo_training_instructor') or user.has_group('gwo_training.group_gwo_training_manager'):
                enrollment = request.env['gwo.enrollment'].sudo().create({
                    'course_id': course.id,
                    'user_id': user.id,
                })
            else:
                return request.render('website.403')
        survey = course.final_exam_id.sudo()
        user_input = survey._create_answer(
            partner=enrollment.user_id.partner_id,
            email=enrollment.user_id.email or enrollment.user_id.partner_id.email,
        )
        user_input.write({
            'state': 'in_progress',
            'gwo_enrollment_id': enrollment.id,
        })
        url = '/survey/start/%s?token=%s' % (survey.id, user_input.token)
        return request.redirect(url)
