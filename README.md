# Course Hub Module

Dieses Repository enthält die Odoo 18 App **Course Hub**. Die Erweiterung orientiert sich an den Kernfunktionen von `website_slides` und `survey`, verzichtet jedoch bewusst auf Gamification- und Karma-Mechaniken.

## Funktionsumfang

* Verwaltung von Kursen mit verantwortlichen Personen und Tags
* Strukturierte Lerninhalte mit kuratierten Templates und hochwertigen Upload-Optionen
* Teilnehmerverwaltung ausschließlich über das Backend mit detaillierter Fortschrittsanzeige
* Fortschrittsverfolgung pro Kurs inklusive Durchschnittswerten
* Vorinstallierte Content-Templates für einen schnellen Start

## Installation

1. Kopiere den Ordner `course_hub` in den `addons`-Pfad deiner Odoo 18 Installation.
2. Aktualisiere die App-Liste in Odoo und installiere **Course Hub**.
3. Lege Kurse an, ergänze Inhalte und verwalte Teilnehmende direkt aus dem Backend.

## Hinweise

* Die App verzichtet auf Gamification-Elemente sowie Karma-Regeln.
* Die Teilnahmeverwaltung erfolgt ausschließlich über das Backend; es werden keine öffentlichen Selbstregistrierungen angeboten.
* List-Views verwenden den neuen View-Typ `list` anstelle von `tree`, wie in Odoo 18 erforderlich.
