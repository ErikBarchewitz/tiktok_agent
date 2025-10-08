# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('-at_install', 'post_install')
class TestGwoCourse(TransactionCase):

    def setUp(self):
        super().setUp()
        self.course = self.env.ref('gwo_training.gwo_course_bstr')
        self.user = self.env['res.users'].create({
            'name': 'Learner Test',
            'login': 'learner@test.example',
            'email': 'learner@test.example',
        })
        self.enrollment = self.env['gwo.enrollment'].create({
            'user_id': self.user.id,
            'course_id': self.course.id,
        })

    def test_progress_computation(self):
        mandatory_contents = self.course.content_ids.filtered('is_mandatory')
        self.assertTrue(mandatory_contents, 'Mandatory contents should exist')
        first_content = mandatory_contents[0]
        result = self.env['gwo.user.result'].create({
            'enrollment_id': self.enrollment.id,
            'content_id': first_content.id,
            'status': 'done',
        })
        self.enrollment._compute_progress_pct()
        self.assertGreater(self.enrollment.progress_pct, 0.0)

    def test_final_exam_score_updates_passed(self):
        self.enrollment.mark_final_score(85.0)
        self.assertTrue(self.enrollment.passed)
        self.assertEqual(self.enrollment.final_exam_score, 85.0)
