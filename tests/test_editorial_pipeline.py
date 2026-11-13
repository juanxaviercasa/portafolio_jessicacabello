"""Regression tests for automatic publication, without touching the live queue."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import publish_article as publisher


class EditorialPipelineTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.queue = self.root / "_queue"
        self.queue.mkdir()
        self.slug = "ejemplo-articulo-prueba"
        self.article = self.queue / ("articulo-001-" + self.slug)
        self.article.mkdir()
        self.meta = {
            "num": 1, "slug": self.slug, "title": "Ejemplo de prueba",
            "excerpt": "Descripción", "category": "comunicacion",
            "category_name": "Expresión Oral", "categories": ["comunicacion"],
            "featured_img": "articulo-001-destacada.webp",
        }
        (self.article / "meta.json").write_text(json.dumps(self.meta), encoding="utf-8")
        (self.article / "index.html").write_text(
            "<html><head></head><body>{{PUBLISH_DATE_SPANISH}} "
            "{{PUBLISH_DATE_ISO}} {{PUBLISH_DATE_SHORT}}</body></html>",
            encoding="utf-8",
        )
        self.patch_root = patch.object(publisher, "REPO_DIR", str(self.root))
        self.patch_queue = patch.object(publisher, "QUEUE_DIR", str(self.queue))
        self.patch_root.start()
        self.patch_queue.start()
        self.addCleanup(self.patch_root.stop)
        self.addCleanup(self.patch_queue.stop)

    def test_publishes_a_queued_article_and_updates_all_indexes(self):
        events = []
        names = ("update_blog_index", "update_category_archive",
                 "update_sitemap", "update_search_index")
        patches = [
            patch.object(publisher, name, side_effect=lambda *args, name=name: events.append(name))
            for name in names
        ]
        for active in patches:
            active.start()
            self.addCleanup(active.stop)
        self.assertTrue(publisher.publish_one())
        destination = self.root / self.slug
        self.assertTrue((destination / "meta.json").is_file())
        contents = (destination / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("{{PUBLISH_DATE", contents)
        self.assertEqual(events, list(names))
        self.assertFalse(self.article.exists())
        self.assertFalse(publisher.publish_one())

    def test_rejects_duplicate_slug_without_deleting_existing_article(self):
        destination = self.root / self.slug
        destination.mkdir()
        existing = destination / "index.html"
        existing.write_text("Artículo original", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            publisher.publish_one()
        self.assertEqual(existing.read_text(encoding="utf-8"), "Artículo original")
        self.assertTrue(self.article.exists())

    def test_missing_meta_is_an_error_not_a_successful_noop(self):
        (self.article / "meta.json").unlink()
        with self.assertRaises(FileNotFoundError):
            publisher.publish_one()

    def test_featured_image_uses_existing_month(self):
        month = self.root / "wp-content/uploads/2026/09"
        month.mkdir(parents=True)
        (month / "articulo-001-destacada.webp").write_bytes(b"mock-image")
        sample = '<html><head></head><body><header class="entry-header"></header></body></html>'
        result = publisher.apply_editorial_layout_to_html(
            sample, self.slug, "Ejemplo", "comunicacion", "Expresión Oral",
            "articulo-001-destacada.webp", "12 de noviembre de 2026",
        )
        self.assertIn("/wp-content/uploads/2026/09/articulo-001-destacada.webp", result)


if __name__ == "__main__":
    unittest.main()
