"""Gancho bíblico Prosperidade e Fé: molde, referência e roteirista."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


def _words(text: str) -> int:
    return len(text.split())


class GanchoBiblicoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        import app.db as db

        self.db = db
        db.DB_PATH = Path(self.tmp.name) / "studio.db"
        db.init_db()

    def test_reference_script_is_channel_specimen(self) -> None:
        from app.services.demo_script import (
            MOISES_NEBO_BEATS,
            MOISES_NEBO_CHANNEL,
            MOISES_NEBO_DURATION_SEC,
            MOISES_NEBO_PASSAGE,
            MOISES_NEBO_SCRIPT,
            MOISES_NEBO_SHORT_BEATS,
            MOISES_NEBO_SHORT_SCRIPT,
            MOISES_NEBO_YOUTUBE_ID,
        )
        from app.services.gancho_biblico import BEATS, VOICE_CUES

        self.assertEqual(len(MOISES_NEBO_BEATS), 10)
        self.assertEqual(len(MOISES_NEBO_SHORT_BEATS), 10)
        self.assertEqual(len(BEATS), 10)
        self.assertEqual(MOISES_NEBO_SCRIPT, " ".join(MOISES_NEBO_BEATS))
        self.assertEqual(MOISES_NEBO_SHORT_SCRIPT, " ".join(MOISES_NEBO_SHORT_BEATS))
        self.assertEqual(MOISES_NEBO_CHANNEL, "Prosperidade e Fé")
        self.assertEqual(MOISES_NEBO_YOUTUBE_ID, "t3xB18IwbFk")
        self.assertEqual(MOISES_NEBO_DURATION_SEC, 184)
        self.assertEqual(MOISES_NEBO_PASSAGE, "Deuteronômio 34")
        self.assertGreaterEqual(_words(MOISES_NEBO_SCRIPT), 350)
        self.assertLessEqual(_words(MOISES_NEBO_SCRIPT), 450)
        self.assertGreaterEqual(_words(MOISES_NEBO_SHORT_SCRIPT), 90)
        self.assertLessEqual(_words(MOISES_NEBO_SHORT_SCRIPT), 180)
        self.assertLess(_words(MOISES_NEBO_SHORT_SCRIPT), _words(MOISES_NEBO_SCRIPT))
        for cue in VOICE_CUES:
            self.assertIn(cue, MOISES_NEBO_SCRIPT, cue)
            self.assertIn(cue, MOISES_NEBO_SHORT_SCRIPT, cue)
        self.assertIn("Monte Nebo", MOISES_NEBO_SCRIPT)
        self.assertIn("120 anos", MOISES_NEBO_SCRIPT)
        self.assertIn("Meribá", MOISES_NEBO_SCRIPT)

    def test_template_apply_fills_beat_markers(self) -> None:
        from app.services.demo_script import MOISES_NEBO_BEATS, MOISES_NEBO_SHORT_BEATS
        from app.services.gancho_biblico import BEATS, VOICE_CUES
        from app.services.story_templates import get_template, list_templates

        ids = {item["id"] for item in list_templates()}
        self.assertIn("gancho_biblico", ids)
        self.assertIn("gancho_biblico_shorts", ids)

        chosen = get_template("gancho_biblico")
        assert chosen is not None
        self.assertEqual(chosen["label"], "Gancho bíblico Prosperidade e Fé")
        paragraphs = [part.strip() for part in chosen["script"].split("\n\n") if part.strip()]
        self.assertEqual(len(paragraphs), 10)
        for paragraph, beat, body in zip(paragraphs, BEATS, MOISES_NEBO_BEATS):
            prefix = f"{beat['label']} — "
            self.assertTrue(paragraph.startswith(prefix), beat["label"])
            self.assertEqual(paragraph[len(prefix):], body)
        for cue in VOICE_CUES:
            self.assertIn(cue, chosen["script"], cue)

        shorts = get_template("gancho_biblico_shorts")
        assert shorts is not None
        short_parts = [part.strip() for part in shorts["script"].split("\n\n") if part.strip()]
        self.assertEqual(len(short_parts), 10)
        self.assertTrue(short_parts[0].startswith("Gancho — "))
        self.assertTrue(short_parts[-1].startswith("Fecho e convite — "))
        self.assertIn(MOISES_NEBO_SHORT_BEATS[4], shorts["script"])

        project = self.db.create_project("Novo", "histórias bíblicas")
        self.db.update_project(
            project["id"],
            script="rascunho antigo",
            scenes_json='[{"index": 0, "title": "velha"}]',
            status="scenes_ready",
        )
        self.db.update_project(
            project["id"],
            script=chosen["script"].strip(),
            scenes_json="[]",
            status="script_ready",
        )
        loaded = self.db.get_project(project["id"])
        assert loaded is not None
        self.assertIn("Gancho — Você sabia", loaded["script"])
        self.assertIn("Âncora bíblica — ", loaded["script"])
        self.assertIn("Detalhe impressionante — ", loaded["script"])
        self.assertIn("Aplicação — Talvez você também", loaded["script"])
        self.assertIn("Fecho e convite — ", loaded["script"])
        self.assertIn("Inscreva-se no canal e ative o sino", loaded["script"])
        self.assertNotIn("rascunho antigo", loaded["script"])
        self.assertEqual(loaded["scenes"], [])
        self.assertEqual(loaded["status"], "script_ready")

    def test_template_production_pacing_and_storyboard(self) -> None:
        from app.services.gancho_biblico import (
            CUT_MAX_SEC,
            CUT_MIN_SEC,
            outline_to_scenes,
            project_production_fields,
            template_uses_production,
        )
        from app.services.scenes import segment_script
        from app.services.story_templates import get_template

        chosen = get_template("gancho_biblico")
        assert chosen is not None
        self.assertTrue(template_uses_production(chosen["id"]))
        fields = project_production_fields()
        self.assertEqual(fields["visual_style"], "semi3d")
        self.assertEqual(fields["burn_captions"], 1)
        self.assertIn("karaokê", fields["brand_caption_style"])
        self.assertIn("verde brilhante", fields["brand_caption_style"])

        scenes = outline_to_scenes(chosen["script"])
        self.assertGreater(len(scenes), 10)
        spoken = " ".join(scene["text"] for scene in scenes)
        self.assertNotIn("Gancho —", spoken)
        self.assertIn("Você sabia que Moisés", spoken)
        self.assertIn("olhos nunca se escureceram", spoken)
        for scene in scenes:
            dur = float(scene["duration_sec"])
            self.assertGreaterEqual(dur, CUT_MIN_SEC)
            self.assertLessEqual(dur, CUT_MAX_SEC)
            self.assertIn("semi-realista", scene["art_note"])
        notes = " ".join(scene["art_note"] for scene in scenes)
        self.assertIn("rolo de pergaminho", notes)
        self.assertIn("paisagem", notes)
        self.assertIn("close dos olhos", notes)
        self.assertIn("Josué mais jovem", notes)
        last = scenes[-1]
        self.assertIn("pessoa de hoje", last["art_note"])
        self.assertIn("gesto de inscrição", last["art_note"])
        self.assertNotIn("Moisés", last["cast"])

        from app.services.images import build_image_prompt

        eye = next(scene for scene in scenes if "close dos olhos" in scene["art_note"])
        prompt = build_image_prompt(
            eye["title"],
            eye["text"],
            0,
            visual_style="semi3d",
            scene_direction=eye["art_note"],
        )
        self.assertIn("semi-realistic 3D", prompt)
        self.assertIn("close dos olhos", prompt)
        self.assertIn("scene direction:", prompt)

        again = segment_script(chosen["script"])
        self.assertEqual([scene["text"] for scene in again], [scene["text"] for scene in scenes])
        plain = segment_script("Um parágrafo só sobre o vale.\n\nOutro sobre o rio.\n\nMais um sobre a noite.\n\nE o último sobre a volta.")
        self.assertEqual(len(plain), 4)
        self.assertNotIn("art_note", plain[0])

    def test_roteirista_nebo_and_new_brief_use_the_voice(self) -> None:
        from app.services.demo_script import MOISES_NEBO_BEATS, MOISES_NEBO_SHORT_BEATS
        from app.services.gancho_biblico import BEATS, VOICE_CUES
        from app.services.planning import compose_plan

        plan = compose_plan(
            "Moisés no monte Nebo, Deuteronômio 34",
            title="Episódio",
            theme="histórias bíblicas",
            brand_name="Prosperidade e Fé",
        )
        self.assertEqual(plan["story_id"], "moises_nebo")
        self.assertEqual(plan["passage"], "Deuteronômio 34")
        roteiro = plan["agents"]["roteirista"]
        scenes = roteiro["scenes"]
        self.assertEqual(" ".join(scene["narration"] for scene in scenes), " ".join(MOISES_NEBO_BEATS))
        self.assertGreater(len(scenes), len(BEATS))
        for scene in scenes:
            self.assertGreaterEqual(float(scene["duration_sec"]), 3)
            self.assertLessEqual(float(scene["duration_sec"]), 6)
        for cue in VOICE_CUES:
            self.assertIn(cue, roteiro["script"], cue)
        self.assertNotIn("Gancho —", roteiro["script"])
        notes = " ".join(note["art_note"] for note in plan["agents"]["diretor_arte"]["scene_notes"])
        self.assertIn("rolo de pergaminho", notes)
        self.assertIn("paisagem", notes)
        self.assertIn("close dos olhos", notes)
        self.assertIn("Josué mais jovem", notes)
        self.assertIn("pessoa de hoje", plan["agents"]["diretor_arte"]["scene_notes"][-1]["art_note"])
        self.assertIn("gesto de inscrição", plan["agents"]["diretor_arte"]["scene_notes"][-1]["art_note"])
        arte = plan["agents"]["diretor_arte"]
        self.assertEqual(arte["visual_style"], "semi3d")
        self.assertIn("verde brilhante", arte["brand_caption_style"])
        self.assertIn("Ken Burns", arte["summary"])
        editor = plan["agents"]["editor_youtube"]
        self.assertTrue(editor["hook"].startswith("Você sabia"))
        self.assertTrue(editor["youtube_description"].startswith(editor["hook"]))
        self.assertIn("Deuteronômio 34", editor["youtube_description"])
        self.assertIn("Prosperidade e Fé", editor["youtube_description"])
        self.assertIn("Inscreva-se no canal e ative o sino", editor["youtube_description"])

        sea = compose_plan("Moisés no mar Vermelho")
        self.assertEqual(sea["story_id"], "moises_mar")
        self.assertNotEqual(sea["agents"]["roteirista"]["scenes"][0]["beat"], "Gancho")

        short = compose_plan("Moisés no monte Nebo shorts")
        self.assertEqual(short["story_id"], "moises_nebo")
        self.assertEqual(
            " ".join(scene["narration"] for scene in short["agents"]["roteirista"]["scenes"]),
            " ".join(MOISES_NEBO_SHORT_BEATS),
        )
        self.assertIn("Versão curta", short["agents"]["roteirista"]["summary"])

        fresh = compose_plan("A parábola do fermento na massa")
        self.assertIsNone(fresh["story_id"])
        fresh_scenes = fresh["agents"]["roteirista"]["scenes"]
        seen: list[str] = []
        for scene in fresh_scenes:
            if not seen or seen[-1] != scene["beat"]:
                seen.append(scene["beat"])
        self.assertEqual(seen, [beat["label"] for beat in BEATS])
        fresh_script = fresh["agents"]["roteirista"]["script"]
        self.assertIn("fermento", fresh_script)
        for cue in VOICE_CUES:
            self.assertIn(cue, fresh_script, cue)
        self.assertGreaterEqual(_words(fresh_script), 300)

        verse = compose_plan("João 3:16 — o amor de Deus")
        self.assertEqual(verse["passage"], "João 3:16")
        self.assertTrue(
            any("João 3:16" in scene["narration"] for scene in verse["agents"]["roteirista"]["scenes"])
        )
        self.assertEqual(verse["agents"]["roteirista"]["scenes"][0]["reference"], "João 3:16")
        self.assertNotIn("visual_style", compose_plan("Rute no campo de Boaz")["agents"]["diretor_arte"])

    def test_prompt_library_voice_block(self) -> None:
        from app.services.prompt_library import apply_block_to_project

        seeds = self.db.list_prompt_blocks(None)
        block = next(item for item in seeds if item["title"] == "Voz do gancho bíblico")
        self.assertEqual(block["category"], "narrativa")
        self.assertEqual(block["target"], "script")
        self.assertIn("Você sabia", block["body"])
        self.assertIn("detalhe impressionante", block["body"])
        self.assertIn("Inscreva-se no canal", block["body"])

        project = self.db.create_project("Novo", "fé")
        patch = apply_block_to_project(project, block)
        self.assertIn("Você sabia", patch["script"])


if __name__ == "__main__":
    unittest.main()
