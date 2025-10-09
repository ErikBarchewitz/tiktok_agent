# -*- coding: utf-8 -*-
"""Website controllers for the learner experience."""

from odoo import http
from odoo.http import request


class AcademyPortal(http.Controller):
    """Route handlers for rendering the player and recording progress."""

    @http.route(['/academy/course/<int:course_id>'], type='http', auth='user', website=True)
    def academy_course(self, course_id, **kwargs):
        channel = request.env['slide.channel'].sudo().browse(course_id)
        if not channel.exists():
            return request.not_found()
        if not request.env.user.has_group('academy_learning.group_academy_user'):
            return request.not_found()
        enrollment = request.env['academy.course.enrollment'].sudo().search([
            ('channel_id', '=', channel.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        if not enrollment and channel.allow_self_enroll:
            enrollment = request.env['academy.course.enrollment'].sudo().create({
                'channel_id': channel.id,
                'user_id': request.env.user.id,
            })
        if enrollment:
            enrollment.ensure_progress_lines()
        values = {
            'course_id': channel.id,
            'content_id': kwargs.get('content_id') or (channel.academy_section_ids[:1].content_ids[:1].id if channel.academy_section_ids else False),
        }
        return request.render('academy_learning.academy_course_player', values)

    @http.route(['/academy/content/<int:content_id>'], type='http', auth='user', website=True)
    def academy_content(self, content_id, **kwargs):
        content = request.env['academy.course.content'].sudo().browse(content_id)
        if not content.exists():
            return request.not_found()
        enrollment = request.env['academy.course.enrollment'].sudo().search([
            ('channel_id', '=', content.section_id.channel_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        if not enrollment:
            return request.redirect('/academy/course/%s' % content.section_id.channel_id.id)
        progress = request.env['academy.course.progress'].sudo().search([
            ('enrollment_id', '=', enrollment.id),
            ('content_id', '=', content.id)
        ], limit=1)
        if progress:
            progress.record_time(0)
        values = {'course_id': content.section_id.channel_id.id, 'content_id': content.id}
        return request.render('academy_learning.academy_course_player', values)

    @http.route(['/academy/quiz/<int:quiz_id>'], type='http', auth='user', methods=['POST'], website=True)
    def academy_quiz_submit(self, quiz_id, **post):
        quiz = request.env['academy.quiz'].sudo().browse(quiz_id)
        if not quiz.exists():
            return request.not_found()
        content = request.env['academy.course.content'].sudo().search([('quiz_id', '=', quiz.id)], limit=1)
        enrollment = request.env['academy.course.enrollment'].sudo().search([
            ('channel_id', '=', content.section_id.channel_id.id),
            ('user_id', '=', request.env.user.id),
        ], limit=1)
        if not enrollment:
            return request.redirect('/academy/course/%s' % content.section_id.channel_id.id)
        lines = []
        for question in quiz.question_ids:
            answer_key = 'q%s' % question.id
            value = post.get(answer_key)
            selected = []
            if question.question_type in ('single', 'boolean'):
                if value:
                    selected.append(int(value))
            elif question.question_type == 'multiple':
                selected = [int(v) for v in post.getlist(answer_key)] if hasattr(post, 'getlist') else [int(v) for v in value.split(',') if v]
            lines.append((0, 0, {
                'question_id': question.id,
                'selected_option_ids': [(6, 0, selected)] if selected else False,
                'free_text_value': value if question.question_type == 'text' else False,
                'is_correct': False,
            }))
        attempt = request.env['academy.quiz.attempt'].sudo().create({
            'quiz_id': quiz.id,
            'user_id': request.env.user.id,
            'enrollment_id': enrollment.id,
            'question_line_ids': lines,
        })
        message = 'Great job!' if attempt.passed else 'Keep trying!'
        return request.render('academy_learning.academy_quiz_result', {
            'attempt': attempt,
            'course_id': content.section_id.channel_id.id,
            'content_id': content.id,
            'message': message,
        })


class AcademyQuizResult(http.Controller):
    @http.route(['/academy/quiz/result/<int:attempt_id>'], type='http', auth='user', website=True)
    def quiz_result(self, attempt_id, **kwargs):
        attempt = request.env['academy.quiz.attempt'].sudo().browse(attempt_id)
        if not attempt.exists():
            return request.not_found()
        return request.render('academy_learning.academy_quiz_result', {
            'attempt': attempt,
            'course_id': attempt.enrollment_id.channel_id.id if attempt.enrollment_id else False,
            'content_id': attempt.question_line_ids[:1].question_id.quiz_id.content_ids[:1].id if attempt.question_line_ids else False,
        })
