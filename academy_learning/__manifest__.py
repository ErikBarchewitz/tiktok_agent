# -*- coding: utf-8 -*-
{
    "name": "Academy Learning",
    "summary": "E-Learning platform with course, content, and quiz management",
    "description": """Academy Learning stellt eine moderne E-Learning-Plattform auf Basis von Odoo 18 bereit.
Sie ermöglicht das einfache Erstellen, Verwalten und Teilen von Kursen inklusive Lektionen,
Quizze und Lernfortschritten. Über einen eindeutigen Link können Lernende einem Kurs beitreten
und den gesamten Content direkt im Web-Frontend absolvieren.""",
    "author": "",
    "website": "",
    "category": "Education",
    "version": "18.0.1.0.0",
    "depends": [
        "base",
        "web",
        "website",
        "portal",
        "mail",
    ],
    "data": [
        "security/academy_learning_groups.xml",
        "security/ir.model.access.csv",
        "data/academy_learning_portal_data.xml",
        "views/assets.xml",
        "views/academy_course_views.xml",
        "views/academy_lesson_views.xml",
        "views/academy_quiz_views.xml",
        "views/academy_enrollment_views.xml",
        "views/academy_wizard_views.xml",
        "views/academy_menu.xml",
        "views/academy_website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "academy_learning/static/src/scss/academy_learning.scss",
        ],
    },
    "application": True,
    "license": "LGPL-3",
    "icon": "/academy_learning/static/description/icon.svg",
}
