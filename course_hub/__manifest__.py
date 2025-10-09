# -*- coding: utf-8 -*-
{
    "name": "Course Hub",
    "summary": "Create structured courses with curated templates and attendee progress tracking.",
    "version": "18.0.1.0.0",
    "category": "Education",
    "author": "Custom",
    "website": "https://example.com",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/course_menus.xml",
        "views/course_views.xml",
        "data/course_templates.xml",
    ],
    "application": True,
    "license": "LGPL-3",
}
