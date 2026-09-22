"""Planejamento da equipe: criação do plano, aplicação e prompt por cena."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class PlanningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        import app.db as db

        self.db = db
        db.DB_PATH = Path(self.tmp.name) / "studio.db"
        db.init_db()

    def test_known_stories_and_generic_brief(self) -> None:
        from app.services.planning import compose_plan, example_briefs
        from app.services.visual import ATMOSPHERES, CAMERAS, LIGHTS

        for brief, story_id in example_briefs():
            plan = compose_plan(
                brief,
                title="Episódio",
                theme="histórias bíblicas",
                series_name="Heróis da fé",
                episode_number=3,
                brand_name="Prosperidade e Fé",
                brand_voice="Reverente e claro.",
                visual_style="cinematic",
            )
            self.assertEqual(plan["story_id"], story_id, brief)
            self.assertEqual(plan["source"], "template")
            self.assertEqual(
                [step["id"] for step in plan["steps"]],
                ["roteirista", "diretor_arte", "editor_youtube"],
            )
            roteiro = plan["agents"]["roteirista"]
            arte = plan["agents"]["diretor_arte"]
            editor = plan["agents"]["editor_youtube"]
            self.assertGreaterEqual(len(roteiro["scenes"]), 4, brief)
            self.assertEqual(len(roteiro["scenes"]), len(arte["scene_notes"]), brief)
            self.assertEqual(roteiro["script"].count("\n\n") + 1, len(roteiro["scenes"]))
            self.assertTrue(roteiro["passage"], brief)
            self.assertIn(roteiro["passage"], editor["youtube_description"])
            self.assertTrue(editor["hook"])
            self.assertTrue(editor["youtube_description"].startswith(editor["hook"]))
            self.assertLessEqual(len(editor["youtube_title"]), 95, brief)
            self.assertIn("Heróis da fé", editor["youtube_title"])
            self.assertIn("Ep. 3", editor["youtube_title"])
            self.assertIn("Prosperidade e Fé", editor["youtube_description"])
            self.assertIn(arte["light_preset"], LIGHTS)
            self.assertIn(arte["atmosphere_preset"], ATMOSPHERES)
            for note in arte["scene_notes"]:
                self.assertIn(note["light"], LIGHTS, brief)
                self.assertIn(note["camera"], CAMERAS, brief)
                self.assertIn(note["atmosphere"], ATMOSPHERES, brief)
                self.assertTrue(note["art_note"], brief)
            for block in arte["library_blocks"]:
                self.assertTrue(block["title"])
                self.assertTrue(block["body"])

        again = compose_plan("Jonas e o grande peixe", title="Jonas", brand_name="Prosperidade e Fé")
        twin = compose_plan("Jonas e o grande peixe", title="Jonas", brand_name="Prosperidade e Fé")
        self.assertEqual(again, twin)

        rute = compose_plan("Rute em Belém colhendo cevada")
        self.assertEqual(rute["story_id"], "rute")

        free = compose_plan("A parábola do fermento na massa")
        self.assertIsNone(free["story_id"])
        self.assertEqual(len(free["agents"]["roteirista"]["scenes"]), 5)
        self.assertIn("fermento", free["agents"]["roteirista"]["script"])
        self.assertIn(
            "Conferir a passagem",
            free["agents"]["roteirista"]["scenes"][0]["reference"],
        )

        verse = compose_plan("João 3:16 — o amor de Deus")
        self.assertIsNone(verse["story_id"])
        self.assertEqual(verse["passage"], "João 3:16")
        self.assertEqual(verse["agents"]["roteirista"]["scenes"][0]["reference"], "João 3:16")

        with self.assertRaises(ValueError):
            compose_plan("   ")

    def test_art_keeps_style_and_uses_prompt_library(self) -> None:
        from app.services.planning import compose_plan

        plan = compose_plan(
            "Quero um vídeo de Davi e Golias para a série",
            title="Série do vale",
            visual_style="watercolor",
            series_name="Gênesis narrado",
            episode_number=4,
            brand_name="Prosperidade e Fé",
        )
        arte = plan["agents"]["diretor_arte"]
        editor = plan["agents"]["editor_youtube"]
        self.assertEqual(plan["story_id"], "davi_golias")
        self.assertIn("Aquarela", arte["summary"])
        self.assertIn("1 Samuel 17", plan["agents"]["roteirista"]["passage"])
        titles = {block["title"] for block in arte["library_blocks"]}
        self.assertIn("Pastor jovem", titles)
        self.assertIn("Close emocional", titles)
        self.assertIn("Série do vale", editor["youtube_title"])
        self.assertNotIn("camera_preset", arte)

    def test_apply_fills_fields_and_keeps_unrelated_settings(self) -> None:
        from app.services.planning import apply_plan_fields, compose_plan

        project = self.db.create_project("Novo projeto", "fé", aspect="9:16")
        pid = project["id"]
        self.db.update_project(
            pid,
            visual_style="watercolor",
            light_preset="moonlight",
            camera_preset="close",
            atmosphere_preset="garden",
            audio_mode="none",
            burn_captions=0,
            series_name="Mulheres da Bíblia",
            episode_number=2,
            prompt_extra="névoa no vale ao amanhecer",
            brand_name="Canal da casa",
            brand_voice="Voz da casa, curta e firme.",
            brand_logo_note="logo dourado no canto",
            scenes_json=self.db.scenes_to_json(
                [
                    {
                        "index": 0,
                        "title": "Antiga",
                        "text": "texto antigo",
                        "cast": "",
                        "image_path": "images/cena-0.jpg",
                        "image_source": "upload",
                        "image_prompt": "prompt antigo",
                        "duration_sec": 8.5,
                    }
                ]
            ),
            youtube_title="titulo antigo",
            script="roteiro antigo",
        )
        loaded = self.db.get_project(pid)
        assert loaded is not None
        plan = compose_plan(
            "Rute no campo de Boaz",
            title=loaded["title"],
            theme=loaded["theme"],
            series_name=loaded["series_name"],
            episode_number=loaded["episode_number"],
            brand_name=loaded["brand_name"],
            brand_voice=loaded["brand_voice"],
            visual_style=loaded["visual_style"],
        )
        saved = self.db.create_production_plan(pid, plan["brief"], plan)
        self.assertEqual(saved["status"], "ready")
        self.assertEqual(saved["plan"]["story_id"], "rute")

        patch = apply_plan_fields(loaded, saved["plan"], script=True, visual=True, youtube=True)
        scenes = patch.pop("scenes")
        self.db.update_project(pid, scenes_json=self.db.scenes_to_json(scenes), **patch)
        self.db.mark_production_plan_applied(saved["id"])

        again = self.db.get_project(pid)
        assert again is not None
        self.assertIn("Rute", again["script"])
        self.assertNotIn("roteiro antigo", again["script"])
        self.assertGreaterEqual(len(again["scenes"]), 4)
        self.assertEqual(again["scenes"][0]["image_path"], "images/cena-0.jpg")
        self.assertEqual(again["scenes"][0]["image_source"], "upload")
        self.assertEqual(again["scenes"][0]["duration_sec"], 8.5)
        self.assertTrue(again["scenes"][0]["art_note"])
        self.assertTrue(again["scenes"][0]["reference"])
        self.assertEqual(again["status"], "scenes_ready")
        self.assertIn("névoa no vale ao amanhecer", again["prompt_extra"])
        self.assertIn("Direção de arte para", again["prompt_extra"])
        self.assertIn("Sem violência gráfica", again["prompt_extra"])
        self.assertEqual(again["light_preset"], plan["agents"]["diretor_arte"]["light_preset"])
        self.assertEqual(
            again["atmosphere_preset"],
            plan["agents"]["diretor_arte"]["atmosphere_preset"],
        )
        self.assertEqual(again["youtube_title"], plan["agents"]["editor_youtube"]["youtube_title"])
        self.assertIn("Canal da casa", again["youtube_description"])
        self.assertIn("Mulheres da Bíblia", again["youtube_title"])

        self.assertEqual(again["visual_style"], "watercolor")
        self.assertEqual(again["camera_preset"], "close")
        self.assertEqual(again["audio_mode"], "none")
        self.assertFalse(again["add_music"])
        self.assertFalse(again["burn_captions"])
        self.assertEqual(again["aspect"], "9:16")
        self.assertEqual(again["series_name"], "Mulheres da Bíblia")
        self.assertEqual(again["episode_number"], 2)
        self.assertEqual(again["brand_name"], "Canal da casa")
        self.assertEqual(again["brand_voice"], "Voz da casa, curta e firme.")
        self.assertEqual(again["brand_logo_note"], "logo dourado no canto")
        self.assertEqual(again["title"], "Novo projeto")

        second = apply_plan_fields(again, saved["plan"], script=False, visual=True, youtube=False)
        self.db.update_project(pid, **second)
        third = self.db.get_project(pid)
        assert third is not None
        self.assertEqual(third["prompt_extra"].count("Direção de arte para"), 1)
        self.assertEqual(third["script"], again["script"])

        marked = self.db.get_production_plan(saved["id"])
        assert marked is not None
        self.assertEqual(marked["status"], "applied")
        self.assertTrue(self.db.delete_project(pid))
        self.assertIsNone(self.db.latest_production_plan(pid))

    def test_apply_youtube_only_leaves_script(self) -> None:
        from app.services.planning import apply_plan_fields, compose_plan

        project = self.db.create_project("Ester", "corte")
        self.db.update_project(project["id"], script="roteiro manual", youtube_title="antigo")
        loaded = self.db.get_project(project["id"])
        assert loaded is not None
        plan = compose_plan("Ester diante do rei", title="Ester", brand_name="Prosperidade e Fé")
        patch = apply_plan_fields(loaded, plan, script=False, visual=False, youtube=True)
        self.assertNotIn("script", patch)
        self.assertNotIn("scenes", patch)
        self.assertNotIn("light_preset", patch)
        self.db.update_project(project["id"], **patch)
        again = self.db.get_project(project["id"])
        assert again is not None
        self.assertEqual(again["script"], "roteiro manual")
        self.assertEqual(again["light_preset"], "")
        self.assertNotEqual(again["youtube_title"], "antigo")
        self.assertTrue(again["youtube_title"])

    def test_scene_direction_reaches_image_prompt(self) -> None:
        from app.services.images import build_image_prompt
        from app.services.planning import scene_prompt_kwargs

        base = {
            "visual_style": "oil",
            "light": "natural",
            "camera": "",
            "atmosphere": "",
            "prompt_extra": "névoa",
            "brand_fragment": "",
        }
        merged = scene_prompt_kwargs(
            base,
            {
                "art_light": "firelight",
                "art_camera": "close",
                "art_atmosphere": "temple",
                "art_note": "lamparinas de barro no altar",
            },
        )
        self.assertEqual(merged["light"], "firelight")
        self.assertEqual(merged["camera"], "close")
        self.assertEqual(merged["atmosphere"], "temple")
        self.assertEqual(merged["visual_style"], "oil")
        self.assertEqual(merged["scene_direction"], "lamparinas de barro no altar")

        untouched = scene_prompt_kwargs(base, {})
        self.assertEqual(untouched["light"], "natural")
        self.assertNotIn("scene_direction", untouched)

        prompt = build_image_prompt(
            "O altar",
            "Elias molha a lenha.",
            0,
            visual_style="oil",
            light=merged["light"],
            camera=merged["camera"],
            atmosphere=merged["atmosphere"],
            scene_direction=merged["scene_direction"],
        )
        self.assertIn("lamparinas de barro no altar", prompt)
        self.assertIn("scene direction:", prompt)
        self.assertIn("oil painting", prompt)
        plain = build_image_prompt("O altar", "Elias molha a lenha.", 0)
        self.assertNotIn("scene direction:", plain)

    def test_plan_roundtrip_and_history(self) -> None:
        from app.services.planning import compose_plan

        project = self.db.create_project("Jonas", "mar")
        first = compose_plan("Jonas e o grande peixe", title="Jonas")
        second = compose_plan("A parábola do fermento na massa", title="Jonas")
        self.db.create_production_plan(project["id"], first["brief"], first)
        latest = self.db.create_production_plan(project["id"], second["brief"], second)
        rows = self.db.list_production_plans(project["id"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], latest["id"])
        self.assertIsNone(rows[0]["plan"]["story_id"])
        self.assertEqual(self.db.latest_production_plan(project["id"])["brief"], second["brief"])


if __name__ == "__main__":
    unittest.main()
