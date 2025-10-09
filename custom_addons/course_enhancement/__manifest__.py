{
    "name": "Enhanced Course Studio",
    "summary": "Backend course management with content templates and participant progress.",
    "version": "18.0.1.0.0",
    "category": "Website/eLearning",
    "website": "https://example.com",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": [
        "website_slides",
        "survey"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/course_menu.xml",
        "views/slide_channel_views.xml",
        "views/slide_channel_partner_views.xml",
        "views/slide_slide_views.xml",
        "views/slide_content_template_views.xml",
        "views/survey_survey_views.xml"
    ],
    "installable": True,
    "application": True,
}
