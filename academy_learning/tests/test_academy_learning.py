# -*- coding: utf-8 -*-
"""Key regression tests for the Academy Learning module."""

import base64
import json
import zipfile
from io import BytesIO

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("academy_learning", "post_install", "-at_install")
class TestAcademyModels(TransactionCase):
    def setUp(self):
        super().setUp()
        self.channel = self.env["slide.channel"].create({
            "name": "Test Course",
        })
        self.section = self.env["academy.course.section"].create({
            "name": "Section",
            "channel_id": self.channel.id,
        })
        self.slide = self.env["slide.slide"].create({
            "name": "Lesson",
            "channel_id": self.channel.id,
            "slide_type": "document",
        })
        self.content = self.env["academy.course.content"].create({
            "slide_id": self.slide.id,
            "section_id": self.section.id,
            "content_kind": "markdown",
        })
        self.user = self.env.ref("base.user_demo")
        self.enrollment = self.env["academy.course.enrollment"].create({
            "channel_id": self.channel.id,
            "user_id": self.user.id,
        })

    def test_progress_lines_created(self):
        self.assertTrue(self.enrollment.progress_line_ids)
        self.assertEqual(self.enrollment.progress_line_ids.content_id, self.content)

    def test_toggle_completion(self):
        line = self.enrollment.progress_line_ids
        line.toggle_complete()
        self.assertTrue(line.is_completed)
        self.assertAlmostEqual(self.enrollment.completion_ratio, 1.0)

    def test_quiz_attempt_scoring(self):
        quiz = self.env["academy.quiz"].create({"name": "Quiz", "passing_score": 1})
        question = self.env["academy.quiz.question"].create(
            {"quiz_id": quiz.id, "name": "Q1", "question_type": "single", "score": 1}
        )
        option = self.env["academy.quiz.answer"].create(
            {"question_id": question.id, "name": "A", "is_correct": True}
        )
        attempt = self.env["academy.quiz.attempt"].create(
            {
                "quiz_id": quiz.id,
                "user_id": self.user.id,
                "enrollment_id": self.enrollment.id,
                "question_line_ids": [
                    (
                        0,
                        0,
                        {
                            "question_id": question.id,
                            "selected_option_ids": [(6, 0, option.ids)],
                            "is_correct": True,
                        },
                    )
                ],
            }
        )
        self.assertTrue(attempt.passed)
        progress = self.enrollment.progress_line_ids.filtered(lambda l: l.content_id.content_kind == "quiz")
        if progress:
            self.assertTrue(progress.is_completed)

    def test_time_spent_recompute(self):
        self.enrollment.progress_line_ids.write({"time_spent": 10})
        self.enrollment.quiz_attempt_ids.write({"time_spent": 5})
        self.enrollment._recompute_time_spent()
        self.assertEqual(self.enrollment.time_spent, 15)


@tagged("academy_learning", "post_install", "-at_install")
class TestImportWizard(TransactionCase):
    def test_import_course_from_zip(self):
        manifest = {
            "course": {"name": "Manifest Course"},
            "sections": [
                {
                    "name": "Intro",
                    "key": "intro",
                    "contents": [
                        {
                            "name": "Welcome",
                            "slide_type": "document",
                            "content_kind": "markdown",
                            "sequence": 1,
                        }
                    ],
                }
            ],
        }
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as zfile:
            zfile.writestr("manifest.json", json.dumps(manifest))
        wizard = self.env["academy.import.wizard"].create({
            "archive": base64.b64encode(buffer.getvalue()),
            "filename": "course.zip",
        })
        action = wizard.action_import()
        self.assertEqual(action["res_model"], "slide.channel")


@tagged("academy_learning", "post_install", "-at_install")
class TestAcademyPortal(HttpCase):
    def setUp(self):
        super().setUp()
        self.user = self.env.ref("base.user_demo")
        self.env.user.groups_id += self.env.ref("academy_learning.group_academy_user")
        self.channel = self.env["slide.channel"].create({"name": "Portal Course", "allow_self_enroll": True})
        self.section = self.env["academy.course.section"].create({"name": "Portal Section", "channel_id": self.channel.id})
        self.slide = self.env["slide.slide"].create({"name": "Portal Lesson", "channel_id": self.channel.id})
        self.content = self.env["academy.course.content"].create({
            "slide_id": self.slide.id,
            "section_id": self.section.id,
            "content_kind": "markdown",
        })

    def test_portal_course_page(self):
        self.authenticate(self.user.login, self.user.password)
        self.url_open("/academy/course/%s" % self.channel.id)
        self.assertIn("Portal Course", self.browser.page_source)
