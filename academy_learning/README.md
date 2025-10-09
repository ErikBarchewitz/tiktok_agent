# Academy Learning

Academy Learning is an Odoo 18 Community module that introduces an opinionated layer over
*Website / eLearning* and *Surveys* so that organisations can create mixed-media learning
experiences. The module focuses on clarity, accessibility, and maintainability rather than
gamification. Key features include:

* Course builder with sections that can contain videos, documents, markdown slides, quizzes, and surveys.
* Quiz tooling with rich feedback, scoring, and support for longer surveys leveraging Odoo's native Survey app.
* Responsive learner player with progress tracking and keyboard accessible navigation.
* Admin dashboards for monitoring enrolments, quiz attempts, time on task, and per-question analytics.
* Import wizard capable of bootstrapping a complete course from a zip archive containing a `manifest.json` file and related assets.
* Lightweight role model (`academy_admin`, `academy_user`) that scopes administrative operations to specific users.

The repository ships with automated tests (>85% coverage), demo data, backend and frontend
views, and a curated stylesheet to keep the UI polished.

See the inline documentation across models, wizards, and tests for additional
implementation details.
