# -*- coding: utf-8 -*-
import json
import uuid

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class AcademyWebsiteController(http.Controller):
    """Website Controller für Academy Learning."""

    def _get_course(self, token):
        course = request.env["academy.course"].sudo().search(
            [("token", "=", token), ("is_published", "=", True)], limit=1
        )
        if not course:
            raise NotFound()
        return course

    def _get_enrollment(self, course, **kwargs):
        enrollment_token = kwargs.get("enrollment_token") or request.params.get("enrollment_token")
        if not enrollment_token:
            enrollment_token = request.session.get("academy_enrollment_token")
        if not enrollment_token:
            return None
        enrollment = request.env["academy.enrollment"].sudo().search(
            [("course_id", "=", course.id), ("access_token", "=", enrollment_token)], limit=1
        )
        if enrollment:
            request.session["academy_enrollment_token"] = enrollment.access_token
        return enrollment

    @http.route("/academy/<string:token>", type="http", auth="public", website=True, sitemap=False)
    def course_portal(self, token, **kwargs):
        course = self._get_course(token)
        enrollment = self._get_enrollment(course, **kwargs)
        values = {
            "course": course,
            "enrollment": enrollment,
            "lessons": course.lesson_ids.sudo(),
            "quizzes": course.quiz_ids.sudo(),
        }
        return request.render("academy_learning.course_portal", values)

    @http.route(
        "/academy/<string:token>/register",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def course_register(self, token, **post):
        course = self._get_course(token)
        name = post.get("name")
        email = post.get("email")
        if not name or not email:
            return request.redirect(f"/academy/{token}?error=missing")

        partner = request.env["res.partner"].sudo().search([("email", "=", email)], limit=1)
        if not partner:
            partner = request.env["res.partner"].sudo().create({"name": name, "email": email})
        else:
            partner.sudo().write({"name": name})

        enrollment = request.env["academy.enrollment"].sudo().search(
            [("course_id", "=", course.id), ("partner_id", "=", partner.id)], limit=1
        )
        if not enrollment:
            enrollment = request.env["academy.enrollment"].sudo().create(
                {
                    "course_id": course.id,
                    "partner_id": partner.id,
                    "access_token": str(uuid.uuid4()),
                    "state": "in_progress",
                }
            )
        request.session["academy_enrollment_token"] = enrollment.access_token
        return request.redirect(f"/academy/{token}?enrollment_token={enrollment.access_token}")

    @http.route(
        "/academy/<string:token>/lesson/<int:lesson_id>/complete",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def lesson_complete(self, token, lesson_id, **post):
        course = self._get_course(token)
        enrollment = self._get_enrollment(course, **post)
        if not enrollment:
            return request.redirect(f"/academy/{token}?error=enroll")
        lesson = request.env["academy.lesson"].sudo().browse(lesson_id)
        if not lesson or lesson.course_id.id != course.id:
            raise NotFound()
        progress_model = request.env["academy.lesson.progress"].sudo()
        progress = progress_model.search(
            [("enrollment_id", "=", enrollment.id), ("lesson_id", "=", lesson.id)], limit=1
        )
        if not progress:
            progress_model.create({"enrollment_id": enrollment.id, "lesson_id": lesson.id})
            enrollment.sudo().recompute_progress()
        return request.redirect(f"/academy/{token}?enrollment_token={enrollment.access_token}#lesson-{lesson_id}")

    @http.route(
        "/academy/<string:token>/quiz/<int:quiz_id>/submit",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def quiz_submit(self, token, quiz_id, **post):
        course = self._get_course(token)
        enrollment = self._get_enrollment(course, **post)
        if not enrollment:
            return request.redirect(f"/academy/{token}?error=enroll")
        quiz = request.env["academy.quiz"].sudo().browse(quiz_id)
        if not quiz or quiz.course_id.id != course.id:
            raise NotFound()

        attempt_count = request.env["academy.quiz.submission"].sudo().search_count(
            [("enrollment_id", "=", enrollment.id), ("quiz_id", "=", quiz.id)]
        )
        if quiz.attempts_allowed and attempt_count >= quiz.attempts_allowed:
            return request.redirect(f"/academy/{token}?error=attempts")

        questions = quiz.question_ids.sudo()
        total_questions = len(questions.filtered(lambda q: q.question_type != "text"))
        score = 0
        submission_answers = {}

        for question in questions:
            field_name = f"question_{question.id}"
            if question.question_type == "text":
                submission_answers[str(question.id)] = post.get(field_name)
                continue
            submitted = (
                request.httprequest.form.getlist(field_name)
                if question.question_type == "multiple"
                else [post.get(field_name)]
            )
            submitted = [value for value in submitted if value]
            submission_answers[str(question.id)] = submitted
            correct_answers = question.correct_answer_ids()
            if not correct_answers:
                continue
            correct_values = set(str(answer.id) for answer in correct_answers)
            submitted_values = set(submitted)
            if question.question_type == "single" and len(submitted_values) == 1 and submitted_values == correct_values:
                score += 1
            elif question.question_type == "multiple" and submitted_values == correct_values:
                score += 1

        percentage = 0.0
        if total_questions:
            percentage = (score / total_questions) * 100

        submission = request.env["academy.quiz.submission"].sudo().create(
            {
                "name": f"{quiz.name} - {enrollment.partner_id.name}",
                "enrollment_id": enrollment.id,
                "quiz_id": quiz.id,
                "score": percentage,
                "is_passed": percentage >= quiz.passing_score,
                "answer_json": json.dumps(submission_answers, ensure_ascii=False),
            }
        )
        enrollment.sudo().write({"quiz_score": percentage})
        enrollment.sudo().recompute_progress()
        request.session["academy_last_submission_id"] = submission.id
        return request.redirect(f"/academy/{token}?enrollment_token={enrollment.access_token}#quiz-{quiz_id}")
