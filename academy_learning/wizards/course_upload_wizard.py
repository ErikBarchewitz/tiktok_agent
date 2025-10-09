# -*- coding: utf-8 -*-
import base64
import io
import json
import zipfile

from odoo import _, fields, models
from odoo.exceptions import UserError


class AcademyCourseUploadWizard(models.TransientModel):
    _name = "academy.course.upload.wizard"
    _description = "Wizard zum Hochladen kompletter Kursinhalte"

    course_id = fields.Many2one("academy.course", required=True)
    data_file = fields.Binary(string="ZIP-Datei", required=True)
    filename = fields.Char(string="Dateiname")
    replace_content = fields.Boolean(
        string="Bestehende Inhalte ersetzen",
        help="Aktivieren, um Lektionen und Quizze des Kurses vor dem Import zu löschen.",
    )
    upload_notes = fields.Text(
        string="Format-Hinweise",
        default=lambda self: _(
            "Die ZIP-Datei muss mindestens eine course.json Datei mit folgendem Grundschema enthalten:\n"
            "{\n  \"course\": {\"name\": \"...\", \"tagline\": \"...\", \"description\": \"...\"},\n"
            "  \"lessons\": [{\"name\": \"...\", \"content\": \"<p>HTML</p>\"}],\n"
            "  \"quizzes\": [{\"name\": \"...\", \"questions\": [{\"name\": \"...\", \"answers\": [{\"name\": \"...\", \"is_correct\": true}]}]}]\n}"
        ),
        readonly=True,
    )

    def action_upload(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Bitte wählen Sie eine ZIP-Datei aus."))

        try:
            raw = base64.b64decode(self.data_file)
        except Exception as exc:
            raise UserError(_("Die Datei konnte nicht dekodiert werden: %s") % exc) from exc

        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if "course.json" not in archive.namelist():
                    raise UserError(_("Die ZIP-Datei enthält keine course.json."))
                with archive.open("course.json") as json_file:
                    payload = json.loads(json_file.read().decode("utf-8"))
        except UserError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            raise UserError(_("Die Kursdatei konnte nicht gelesen werden: %s") % exc) from exc

        course_vals = payload.get("course", {})
        lesson_vals = payload.get("lessons", [])
        quiz_vals = payload.get("quizzes", [])

        course = self.course_id
        if course_vals:
            course.write({key: value for key, value in course_vals.items() if key in {"name", "tagline", "description"}})

        if self.replace_content:
            course.lesson_ids.unlink()
            course.quiz_ids.unlink()

        lesson_records = []
        for sequence, data in enumerate(lesson_vals, start=10):
            lesson_values = {
                "name": data.get("name") or (_("Lektion %s") % (sequence - 9)),
                "sequence": data.get("sequence", sequence),
                "content": data.get("content", ""),
                "duration_minutes": data.get("duration_minutes", 0),
                "resource_url": data.get("resource_url"),
                "course_id": course.id,
            }
            lesson_records.append(lesson_values)
        if lesson_records:
            self.env["academy.lesson"].create(lesson_records)

        for quiz_data in quiz_vals:
            quiz = self.env["academy.quiz"].create(
                {
                    "name": quiz_data.get("name", _("Neues Quiz")),
                    "course_id": course.id,
                    "sequence": quiz_data.get("sequence", 10),
                    "introduction": quiz_data.get("introduction", ""),
                    "passing_score": quiz_data.get("passing_score", 60),
                    "attempts_allowed": quiz_data.get("attempts_allowed", 0),
                }
            )
            for question_sequence, question_data in enumerate(quiz_data.get("questions", []), start=10):
                question = self.env["academy.quiz.question"].create(
                    {
                        "name": question_data.get("name", _("Neue Frage")),
                        "quiz_id": quiz.id,
                        "sequence": question_data.get("sequence", question_sequence),
                        "question_type": question_data.get("question_type", "single"),
                        "explanation": question_data.get("explanation"),
                    }
                )
                answers = []
                for answer_sequence, answer_data in enumerate(question_data.get("answers", []), start=10):
                    answers.append(
                        {
                            "name": answer_data.get("name", _("Antwort")),
                            "question_id": question.id,
                            "sequence": answer_data.get("sequence", answer_sequence),
                            "is_correct": bool(answer_data.get("is_correct", False)),
                        }
                    )
                if answers:
                    self.env["academy.quiz.answer"].create(answers)

        course.invalidate_cache()
        return {
            "type": "ir.actions.act_window_close",
        }
