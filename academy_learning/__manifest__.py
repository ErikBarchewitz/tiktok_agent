# -*- coding: utf-8 -*-
{
    "name": "Academy Learning",
    "summary": "Create and deliver e-learning experiences integrated with quizzes and surveys.",
    "version": "18.0.1.0.0",
    "author": "OpenAI",
    "website": "https://www.example.com",
    "category": "Education",
    "license": "LGPL-3",
    "depends": [
        "website_slides",
        "survey"
    ],
    "data": [
        "security/academy_security.xml",
        "security/ir.model.access.csv",
        "views/academy_menu.xml",
        "views/academy_course_views.xml",
        "views/academy_section_views.xml",
        "views/academy_content_views.xml",
        "views/academy_quiz_views.xml",
        "views/academy_import_views.xml",
        "views/academy_templates.xml",
        "wizards/academy_import_wizard_views.xml",
        "demo/academy_demo.xml"
    ],
    "demo": [
        "demo/academy_demo.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "academy_learning/static/src/css/academy_player.css"
        ],
        "web.assets_backend": [
            "academy_learning/static/src/css/academy_backend.css"
        ]
    },
    "installable": True,
    "application": True
}
