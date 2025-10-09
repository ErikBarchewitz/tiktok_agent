# -*- coding: utf-8 -*-
"""Wizard that allows the import of a course from a structured archive."""

import base64
import io
import json
import zipfile

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class AcademyImportWizard(models.TransientModel):
    _name = "academy.import.wizard"
    _description = "Academy Course Import"

    archive = fields.Binary(string="Archive", required=True, help="Zip file with manifest.json")
    filename = fields.Char()
    auto_publish = fields.Boolean(default=True)

    def _load_manifest(self, data):
        try:
            manifest = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValidationError(_("Invalid manifest.json file: %s") % exc) from exc
        required = {"course", "sections"}
        if not required.issubset(manifest):
            raise ValidationError(_("Manifest missing keys: %s") % ", ".join(sorted(required - manifest.keys())))
        return manifest

    def _import_quiz(self, quiz_dict):
        Quiz = self.env["academy.quiz"]
        Quiz.validate_manifest_dict(quiz_dict)
        quiz = Quiz.create({"name": quiz_dict["name"], "passing_score": quiz_dict.get("passing_score", 0.0)})
        for question_dict in quiz_dict.get("questions", []):
            question = self.env["academy.quiz.question"].create(
                {
                    "quiz_id": quiz.id,
                    "name": question_dict["name"],
                    "question_type": question_dict.get("question_type", "single"),
                    "score": question_dict.get("score", 1.0),
                    "feedback_correct": question_dict.get("feedback_correct"),
                    "feedback_incorrect": question_dict.get("feedback_incorrect"),
                }
            )
            for option_dict in question_dict.get("options", []):
                self.env["academy.quiz.answer"].create(
                    {
                        "question_id": question.id,
                        "name": option_dict["name"],
                        "is_correct": option_dict.get("is_correct", False),
                        "sequence": option_dict.get("sequence", 10),
                        "value": option_dict.get("value"),
                    }
                )
        return quiz

    def _load_attachment(self, zfile, asset_path, channel):
        content = zfile.read(asset_path)
        attachment = self.env["ir.attachment"].create(
            {
                "name": asset_path.split("/")[-1],
                "datas": base64.b64encode(content),
                "res_model": "slide.channel",
                "res_id": channel.id,
            }
        )
        return attachment

    def action_import(self):
        self.ensure_one()
        if not self.archive:
            raise UserError(_("Please upload a zip archive."))
        stream = io.BytesIO(base64.b64decode(self.archive))
        try:
            with zipfile.ZipFile(stream) as zfile:
                if "manifest.json" not in zfile.namelist():
                    raise ValidationError(_("Archive must include a manifest.json file."))
                manifest = self._load_manifest(zfile.read("manifest.json"))
                course_vals = manifest["course"]
                channel = self.env["slide.channel"].create(
                    {
                        "name": course_vals["name"],
                        "description": course_vals.get("description"),
                        "is_published": bool(self.auto_publish),
                    }
                )
                sections = {}
                for section_dict in manifest.get("sections", []):
                    section = self.env["academy.course.section"].create(
                        {
                            "name": section_dict["name"],
                            "channel_id": channel.id,
                            "sequence": section_dict.get("sequence", 10),
                            "description": section_dict.get("description"),
                        }
                    )
                    sections[section_dict["key"]] = section
                    for content_dict in section_dict.get("contents", []):
                        slide = self.env["slide.slide"].create(
                            {
                                "name": content_dict["name"],
                                "channel_id": channel.id,
                                "slide_type": content_dict.get("slide_type", "document"),
                                "is_published": bool(self.auto_publish),
                            }
                        )
                        content_vals = {
                            "slide_id": slide.id,
                            "section_id": section.id,
                            "content_kind": content_dict.get("content_kind", "markdown"),
                            "sequence": content_dict.get("sequence", 10),
                        }
                        if content_dict.get("content_kind") == "quiz":
                            quiz = self._import_quiz(content_dict["quiz"])
                            content_vals["quiz_id"] = quiz.id
                        if content_dict.get("content_kind") == "survey" and content_dict.get("survey_ref"):
                            survey = self.env["survey.survey"].search([("access_token", "=", content_dict["survey_ref"])], limit=1)
                            content_vals["survey_id"] = survey.id
                        content = self.env["academy.course.content"].create(content_vals)
                        slide.write({"academy_content_id": content.id})
                        asset_path = content_dict.get("asset")
                        if asset_path and asset_path in zfile.namelist():
                            attachment = self._load_attachment(zfile, asset_path, channel)
                            slide.write({"attachment_id": attachment.id})
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "slide.channel",
                    "res_id": channel.id,
                    "view_mode": "form",
                }
        except zipfile.BadZipFile as exc:
            raise ValidationError(_("Uploaded file is not a valid zip archive.")) from exc
