"""Controles de estilo, áudio, modelos e série — sem rede e sem FFmpeg."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class StudioControlsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        import app.db as db

        self.db = db
        db.DB_PATH = Path(self.tmp.name) / "studio.db"
        db.init_db()

    def test_style_light_camera_atmosphere_and_series_persist(self) -> None:
        project = self.db.create_project("Noé e a arca", "dilúvio")
        self.assertEqual(project["visual_style"], "cinematic")
        self.assertEqual(project["audio_mode"], "both")
        self.assertTrue(project["add_music"])

        updated = self.db.update_project(
            project["id"],
            visual_style="watercolor",
            light_preset="moonlight",
            camera_preset="low",
            atmosphere_preset="storm",
            audio_mode="none",
            series_name="  Gênesis narrado  ",
            episode_number="4",
        )
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["visual_style"], "watercolor")
        self.assertEqual(updated["light_preset"], "moonlight")
        self.assertEqual(updated["camera_preset"], "low")
        self.assertEqual(updated["atmosphere_preset"], "storm")
        self.assertEqual(updated["audio_mode"], "none")
        self.assertFalse(updated["add_music"])
        self.assertEqual(updated["series_name"], "Gênesis narrado")
        self.assertEqual(updated["episode_number"], 4)

        again = self.db.get_project(project["id"])
        assert again is not None
        self.assertEqual(again["atmosphere_preset"], "storm")
        self.assertEqual(again["episode_number"], 4)
        listed = self.db.list_projects()
        self.assertEqual(listed[0]["series_name"], "Gênesis narrado")

    def test_unknown_presets_fall_back(self) -> None:
        project = self.db.create_project("Rute", "colheita")
        updated = self.db.update_project(
            project["id"],
            visual_style="neon-cyber",
            light_preset="laser",
            camera_preset="drone",
            atmosphere_preset="cidade",
            episode_number="0",
        )
        assert updated is not None
        self.assertEqual(updated["visual_style"], "cinematic")
        self.assertEqual(updated["light_preset"], "")
        self.assertEqual(updated["camera_preset"], "")
        self.assertEqual(updated["atmosphere_preset"], "")
        self.assertIsNone(updated["episode_number"])

    def test_audio_modes_sync_music_flag(self) -> None:
        project = self.db.create_project("Davi", "fé")
        music_only = self.db.update_project(project["id"], audio_mode="music")
        assert music_only is not None
        self.assertEqual(music_only["audio_mode"], "music")
        self.assertTrue(music_only["add_music"])

        narration = self.db.update_project(project["id"], audio_mode="narration")
        assert narration is not None
        self.assertFalse(narration["add_music"])

        legacy = self.db.update_project(project["id"], add_music=1)
        assert legacy is not None
        self.assertEqual(legacy["audio_mode"], "both")

    def test_empty_audio_mode_backfill(self) -> None:
        project = self.db.create_project("Ester", "corte")
        conn = self.db.get_conn()
        conn.execute(
            "UPDATE projects SET audio_mode = '', add_music = 0 WHERE id = ?",
            (project["id"],),
        )
        conn.commit()
        conn.close()
        self.db.init_db()
        loaded = self.db.get_project(project["id"])
        assert loaded is not None
        self.assertEqual(loaded["audio_mode"], "narration")
        self.assertFalse(loaded["add_music"])

    def test_image_prompt_includes_style_blocks(self) -> None:
        from app.services.images import build_image_prompt
        from app.services.visual import STYLES, project_visual_kwargs

        default = build_image_prompt("O vale", "O gigante desafia o exército.", 0)
        self.assertIn("photorealistic", default)
        self.assertIn("warm cinematic light", default)
        self.assertNotIn("oil painting", default)
        self.assertIn("Biblical story scene: O vale.", default)

        project = self.db.create_project("Golias", "vale")
        saved = self.db.update_project(
            project["id"],
            visual_style="oil",
            light_preset="rembrandt",
            camera_preset="wide",
            atmosphere_preset="desert",
        )
        prompt = build_image_prompt(
            "O vale",
            "O gigante desafia o exército.",
            1,
            compact=True,
            **project_visual_kwargs(saved),
        )
        self.assertIn("oil painting", prompt)
        self.assertIn("Rembrandt", prompt)
        self.assertIn("wide establishing shot", prompt)
        self.assertIn("Judean desert", prompt)
        self.assertNotIn("warm cinematic light", prompt)

        for key, spec in STYLES.items():
            block = build_image_prompt("Cena", "Texto curto.", 0, visual_style=key)
            token = spec["prompt"].split(",")[0]
            self.assertIn(token, block)

        natural = build_image_prompt(
            "Cena",
            "Texto.",
            0,
            visual_style="cinematic",
            light="natural",
        )
        self.assertIn("natural daylight", natural)
        self.assertNotIn("warm cinematic light", natural)

    def test_story_templates_apply_outline(self) -> None:
        from app.services import story_templates

        templates = story_templates.list_templates()
        self.assertGreaterEqual(len(templates), 4)
        ids = {item["id"] for item in templates}
        self.assertTrue(
            {"queda_graca", "confronto_fe", "chamado_obediencia", "julgamento_alianca"} <= ids
        )
        for item in templates:
            paragraphs = [p for p in item["script"].split("\n\n") if p.strip()]
            self.assertGreaterEqual(len(paragraphs), 4, item["id"])
            self.assertTrue(item["label"])
            self.assertIn(".", item["script"])

        project = self.db.create_project("Novo", "histórias bíblicas")
        self.db.update_project(
            project["id"],
            script="rascunho antigo",
            scenes_json='[{"index": 0, "title": "velha"}]',
            status="scenes_ready",
        )
        chosen = story_templates.get_template("chamado_obediencia")
        assert chosen is not None
        self.db.update_project(
            project["id"],
            script=chosen["script"].strip(),
            scenes_json="[]",
            status="script_ready",
        )
        loaded = self.db.get_project(project["id"])
        assert loaded is not None
        self.assertIn("Moisés", loaded["script"])
        self.assertEqual(loaded["scenes"], [])
        self.assertEqual(loaded["status"], "script_ready")
        self.assertIsNone(story_templates.get_template("nao-existe"))

    def test_youtube_defaults_include_series(self) -> None:
        from app.services.publish import generate_metadata

        meta = generate_metadata(
            "A arca",
            "dilúvio",
            "Noé construiu a arca com a família.\n\nAs águas cobriram a terra.",
            series_name="Gênesis narrado",
            episode_number=4,
            brand_name="Prosperidade e Fé",
        )
        self.assertIn("Gênesis narrado", meta["youtube_title"])
        self.assertIn("Ep. 4", meta["youtube_title"])
        self.assertIn("Prosperidade e Fé", meta["youtube_title"])
        self.assertIn("Série: Gênesis narrado", meta["youtube_description"])
        self.assertIn("Episódio 4", meta["youtube_description"])
        self.assertIn("Canal: Prosperidade e Fé", meta["youtube_description"])
        self.assertIn("Gênesis narrado", meta["youtube_tags"])
        self.assertLessEqual(len(meta["youtube_title"]), 95)

        plain = generate_metadata(
            "Davi e Golias",
            "fé",
            "Um jovem desce ao vale.",
            brand_name="Prosperidade e Fé",
        )
        self.assertIn("Prosperidade e Fé", plain["youtube_title"])
        self.assertNotIn("Série:", plain["youtube_description"])

    def test_prompt_library_save_apply_delete(self) -> None:
        from app.services.prompt_library import apply_block_to_project

        seeds = self.db.list_prompt_blocks(None)
        self.assertGreaterEqual(len(seeds), 8)
        titles = {b["title"] for b in seeds}
        self.assertIn("Luz de templo", titles)
        self.assertIn("Narração acolhedora", titles)

        project = self.db.create_project("Elias", "profeta")
        block = self.db.create_prompt_block(
            title="Fogo no monte",
            body="Chama viva no altar de pedra, fumaça e céu escuro.",
            category="cena",
            target="prompt_extra",
            project_id=project["id"],
        )
        listed = self.db.list_prompt_blocks(project["id"])
        self.assertTrue(any(b["id"] == block["id"] for b in listed))

        patch = apply_block_to_project(project, block)
        self.assertIn("prompt_extra", patch)
        self.db.update_project(project["id"], **patch)
        loaded = self.db.get_project(project["id"])
        assert loaded is not None
        self.assertIn("Chama viva no altar", loaded["prompt_extra"])

        script_block = next(b for b in seeds if b["target"] == "script")
        patch2 = apply_block_to_project(loaded, script_block)
        self.db.update_project(project["id"], **patch2, status="script_ready")
        again = self.db.get_project(project["id"])
        assert again is not None
        self.assertIn(script_block["body"][:40], again["script"])

        self.assertTrue(self.db.delete_prompt_block(block["id"]))
        self.assertFalse(self.db.delete_prompt_block(seeds[0]["id"]))  # seed protegida
        self.assertIsNone(self.db.get_prompt_block(block["id"]))

    def test_brand_fields_in_image_prompt_and_metadata(self) -> None:
        from app.services.brand import compose_brand_prompt_fragment
        from app.services.images import build_image_prompt
        from app.services.publish import generate_metadata
        from app.services.visual import project_visual_kwargs

        project = self.db.create_project("Rute", "redenção")
        self.assertEqual(project["brand_name"], "Prosperidade e Fé")
        self.assertIn("Reverente", project["brand_voice"])

        updated = self.db.update_project(
            project["id"],
            brand_name="Prosperidade e Fé",
            brand_palette="dourado e azul noite",
            brand_visual_notes="rostos consistentes, sem neon",
            prompt_extra="névoa no vale ao amanhecer",
            series_name="Mulheres da Bíblia",
            episode_number=2,
        )
        assert updated is not None
        fragment = compose_brand_prompt_fragment(updated)
        self.assertIn("Prosperidade e Fé", fragment)
        self.assertIn("dourado e azul noite", fragment)
        self.assertIn("rostos consistentes", fragment)

        prompt = build_image_prompt(
            "O campo",
            "Rute colhe nas espigas.",
            0,
            **project_visual_kwargs(updated),
        )
        self.assertIn("Prosperidade e Fé", prompt)
        self.assertIn("dourado e azul noite", prompt)
        self.assertIn("névoa no vale ao amanhecer", prompt)

        meta = generate_metadata(
            updated["title"],
            updated["theme"],
            "Rute colhe nas espigas.",
            series_name=updated["series_name"],
            episode_number=updated["episode_number"],
            brand_name=updated["brand_name"],
            brand_voice=updated["brand_voice"],
            brand_caption_style=updated["brand_caption_style"],
        )
        self.assertIn("Prosperidade e Fé", meta["youtube_title"])
        self.assertIn("Mulheres da Bíblia", meta["youtube_title"])
        self.assertIn("Canal: Prosperidade e Fé", meta["youtube_description"])
        self.assertIn("Tom:", meta["youtube_description"])
        self.assertIn("Legendas:", meta["youtube_description"])
        self.assertIn("Prosperidade e Fé", meta["youtube_tags"])

    def test_audio_mode_and_duration_helpers(self) -> None:
        from app.services.audio_mode import resolve_mode, uses_music, uses_narration
        from app.services.scenes import ensure_durations

        self.assertEqual(resolve_mode(None, music=True), "both")
        self.assertEqual(resolve_mode(None, music=False), "narration")
        self.assertEqual(resolve_mode("music", music=False), "music")
        self.assertEqual(resolve_mode("bogus", music=True), "both")
        self.assertTrue(uses_narration("both"))
        self.assertFalse(uses_narration("none"))
        self.assertTrue(uses_music("music"))
        self.assertFalse(uses_music("narration"))

        scenes = [{"text": "um dois tres quatro cinco", "duration_sec": None}]
        ensure_durations(scenes)
        self.assertGreaterEqual(scenes[0]["duration_sec"], 3)
        scenes[0]["duration_sec"] = 8.5
        ensure_durations(scenes)
        self.assertEqual(scenes[0]["duration_sec"], 8.5)


if __name__ == "__main__":
    unittest.main()
