"""Unit tests for tools/run_perf_capture_v1.py. No Unreal process is started.

Run: python -m unittest tools/test_run_perf_capture_v1.py   (or python tools/test_run_perf_capture_v1.py)
Fixtures: tools/fixtures/perf_capture_v1/run.csv and run.log are a synthetic 7.5 s capture:
1 s warmup with a 50 ms frame, a shader-compile window around 2.2 s (40 ms frame), an F5
reload at 3.0 s (400 ms LoadMap frame then three 45 ms frames), a PSO-miss hitch at 5.5 s,
three GC pauses (1.2, 2.5, 0.8 ms) and PhysicalUsedMB rising 1000 -> 1050 MB.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_perf_capture_v1 as perf  # noqa: E402

FIXTURES = HERE / "fixtures" / "perf_capture_v1"
CSV = FIXTURES / "run.csv"
LOG = FIXTURES / "run.log"
BASE_ARGS = ["--duration", "6", "--warmup", "1", "--mem-interval", "2"]


def args(*extra):
    return perf.parse_args([*BASE_ARGS, *extra])


class Workspace(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def variant(self, name, source, edit):
        text = source.read_bytes().decode("utf-8")
        path = self.tmp / name
        path.write_bytes(edit(text).encode("utf-8"))
        return path

    def edit_csv_frames(self, name, change):
        """Apply change(time_s, row) -> row to every data row of the fixture CSV."""
        lines = CSV.read_bytes().decode("utf-8").split("\n")
        out, elapsed = [lines[0]], 0.0
        for line in lines[1:]:
            if not line or line.startswith("EVENTS") or line.startswith("["):
                out.append(line)
                continue
            row = line.split(",")
            ft = float(row[1])
            out.append(",".join(change(elapsed, row)))
            elapsed += ft / 1000.0
        path = self.tmp / name
        path.write_bytes("\n".join(out).encode("utf-8"))
        return path


class PercentileTests(unittest.TestCase):
    def test_linear_percentiles(self):
        values = list(range(1, 101))
        self.assertAlmostEqual(perf.percentile(values, 50), 50.5)
        self.assertAlmostEqual(perf.percentile(values, 95), 95.05)
        self.assertAlmostEqual(perf.percentile(values, 99), 99.01)
        s = perf.stats(values)
        self.assertEqual((s["samples"], s["max"]), (100, 100))
        self.assertIsNone(perf.percentile([], 95))

    def test_csv_header_at_end_and_metadata(self):
        profile = perf.parse_profile_csv(CSV)
        self.assertIn("PSO/PSOMissesOnHitch", profile["header"])
        self.assertEqual(profile["metadata"]["gpu"], "NVIDIA GeForce RTX 5080")
        self.assertEqual(profile["frames"][-1]["events"][0]["text"], "Cmd: csvprofile stop")
        self.assertIsNone(profile["frames"][0]["values"]["PSO/PSOMissesOnHitch"])  # short early rows


class PassFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code, cls.summary, cls.rows, cls.hitches = perf.analyze(CSV, LOG, args())

    def test_pass_and_exit_code(self):
        self.assertEqual(self.summary["invalid_reasons"], [])
        self.assertEqual((self.summary["verdict"], self.code), ("pass", 0))

    def test_p95_uses_gated_play_frames(self):
        ft = self.summary["metrics_ms"]["FrameTime"]
        self.assertAlmostEqual(ft["gated_play"]["p95"], 7.0)
        self.assertAlmostEqual(ft["gated_play"]["max"], 7.0)
        self.assertAlmostEqual(ft["all_frames"]["max"], 400.0)
        for label in ("GameThread", "RenderThread", "GPU", "RHIThread", "DrawCalls"):
            self.assertIn(label, self.summary["metrics_ms"])

    def test_hitch_phases(self):
        phases = {round(h["frame_ms"]): h["phase"] for h in self.hitches}
        self.assertEqual(phases[50], "warmup")
        self.assertEqual(phases[40], "shader_compile")
        self.assertEqual(phases[400], "f5_reload")
        self.assertEqual(phases[45], "f5_reload")
        self.assertEqual(phases[36], "shader_compile")  # PSO miss frame
        self.assertFalse(any(h["gated"] for h in self.hitches))
        limiter = {round(h["frame_ms"]): h["limiter"] for h in self.hitches}
        self.assertEqual((limiter[50], limiter[40], limiter[400]), ("RenderThread", "GPU", "GameThread"))

    def test_reload_duration_and_actor_counts(self):
        (reload,) = self.summary["reloads"]
        self.assertEqual(reload["source"], "log")
        self.assertAlmostEqual(reload["start_s"], 3.0, places=3)
        self.assertAlmostEqual(reload["duration_s"], 0.535, delta=0.02)
        self.assertEqual((reload["actors_before"], reload["actors_after"]), (25, 25))
        self.assertAlmostEqual(reload["window"][1], 4.5, places=3)
        self.assertTrue(self.summary["checks"]["reload_time"]["pass"])

    def test_shader_window(self):
        (window,) = self.summary["shader_compile_windows_s"]
        self.assertAlmostEqual(window[0], 1.5, places=2)
        self.assertAlmostEqual(window[1], 2.8, places=2)

    def test_memory_growth(self):
        mem = self.summary["memory"]
        self.assertGreaterEqual(len(mem["samples"]), 3)
        self.assertAlmostEqual(mem["samples"][0]["time_s"], 1.0, delta=0.01)
        self.assertAlmostEqual(mem["growth_pct"], 4.0, delta=0.3)

    def test_gc_parse(self):
        gc = self.summary["gc"]
        self.assertEqual(gc["count"], 3)
        self.assertAlmostEqual(gc["max_ms"], 2.5)
        self.assertAlmostEqual(gc["p95_ms"], perf.percentile([1.2, 2.5, 0.8], 95))
        self.assertEqual(gc["purge_count"], 1)

    def test_header_read_back(self):
        h = self.summary["header"]
        self.assertEqual((h["t.MaxFPS"], h["r.VSync"]), ("0", "0"))
        self.assertEqual(h["resolution"], [1920.0, 1080.0])
        self.assertEqual(h["rhi"], "D3D12")
        self.assertEqual(h["scalability_cvars"]["ShadowQuality"], "3")
        self.assertEqual(h["scalability_sections_applied"]["ViewDistanceQuality"], 3)
        self.assertTrue(all(c["status"] == "ok" for c in self.summary["header_checks"]))
        self.assertAlmostEqual(self.summary["load_times"]["startup_loadmap_s"], 1.2)


class FailureTests(Workspace):
    def test_hitch_outside_windows_fails(self):
        def change(t, row):
            if 5.0 <= t < 5.006:
                row[1], row[4] = "40.0000", "39.0000"
            return row
        csv_path = self.edit_csv_frames("hitch.csv", change)
        code, summary, _, hitches = perf.analyze(csv_path, LOG, args())
        self.assertEqual(code, 1)
        gated = [h for h in hitches if h["gated"]]
        self.assertEqual(len(gated), 1)
        self.assertEqual((gated[0]["phase"], gated[0]["limiter"]), ("play", "GPU"))
        self.assertFalse(summary["checks"]["hitches_outside_windows"]["pass"])

    def test_memory_growth_over_threshold_fails(self):
        def change(t, row):
            row[7] = f"{1000 + 300 * t / 7.5:.2f}"
            return row
        code, summary, _, _ = perf.analyze(self.edit_csv_frames("mem.csv", change), LOG, args())
        self.assertEqual(code, 1)
        self.assertGreater(summary["memory"]["growth_pct"], 10)
        self.assertFalse(summary["checks"]["memory_growth"]["pass"])

    def test_p95_threshold_cli(self):
        code, summary, _, _ = perf.analyze(CSV, LOG, args("--p95-ms", "6.5"))
        self.assertEqual(code, 1)
        self.assertFalse(summary["checks"]["p95_frame_time"]["pass"])

    def test_header_mismatch_is_invalid(self):
        log = self.variant("maxfps.log", LOG, lambda s: s.replace('t.MaxFPS = "0"      LastSetBy', 't.MaxFPS = "60"      LastSetBy'))
        code, summary, _, _ = perf.analyze(CSV, log, args())
        self.assertEqual((code, summary["verdict"]), (2, "invalid"))
        self.assertTrue(any("t.MaxFPS mismatch" in r for r in summary["invalid_reasons"]))

    def test_resolution_mismatch_is_invalid(self):
        csv_path = self.variant("res.csv", CSV, lambda s: s.replace("[systemresolution.resx],1920", "[systemresolution.resx],1280"))
        code, summary, _, _ = perf.analyze(csv_path, LOG, args())
        self.assertEqual(code, 2)
        self.assertTrue(any("resolution" in r for r in summary["invalid_reasons"]))

    def test_missing_cvar_echo_is_invalid(self):
        log = self.variant("novsync.log", LOG, lambda s: "\r\n".join(l for l in s.split("\r\n") if "r.VSync" not in l))
        code, summary, _, _ = perf.analyze(CSV, log, args())
        self.assertEqual(code, 2)
        self.assertTrue(any("r.VSync missing" in r for r in summary["invalid_reasons"]))

    def test_short_capture_is_invalid(self):
        code, summary, _, _ = perf.analyze(CSV, LOG, perf.parse_args(["--duration", "60", "--warmup", "1"]))
        self.assertEqual(code, 2)
        self.assertTrue(any("Capture covers" in r for r in summary["invalid_reasons"]))

    def test_no_reload_markers(self):
        log = self.variant("nof5.log", LOG, lambda s: s.replace("LogLoad: LoadMap: /Game/Maps/TeddyEncounter\r\n", "")
                           .replace("LogLoad: Took 0.400000", "LogLoad: Skipped 0.400000"))
        code, summary, _, _ = perf.analyze(CSV, log, args())
        self.assertEqual(code, 2)
        self.assertTrue(any("No F5 reload" in r for r in summary["invalid_reasons"]))
        code, summary, _, hitches = perf.analyze(CSV, log, args("--no-require-reload"))
        self.assertEqual(code, 1)  # the reload frames are now gated hitches
        self.assertTrue(any(h["gated"] and h["frame_ms"] == 400 for h in hitches))

    def test_heuristic_reload_without_log(self):
        code, summary, _, hitches = perf.analyze(CSV, None, args())
        self.assertEqual(summary["reload_detection"], "heuristic")
        self.assertEqual(summary["reloads"][0]["source"], "heuristic")
        self.assertTrue(any("heuristic" in w for w in summary["warnings"]))
        self.assertEqual(code, 2)  # t.MaxFPS / r.VSync cannot be read back without the log


class CliTests(Workspace):
    def test_dry_run_prints_command(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = perf.main(["--dry-run", "--engine-root", "C:/UE_5.8", "--out", str(self.tmp / "out")])
        text = buffer.getvalue()
        self.assertEqual(code, 0)
        for part in ("UnrealEditor.exe", "TeddyBlueprint.uproject", "/Game/Maps/TeddyEncounter", " -game ",
                     "-windowed", "-ResX=1920", "-ResY=1080", "-ForceRes", "-csvGpuStats",
                     "-dpcvars=t.MaxFPS=0,r.VSync=0", "t.MaxFPS 0,r.VSync 0", "csvprofile start",
                     "LogGarbage Log", "-abslog=", "engine.log"):
            self.assertIn(part, text)
        self.assertFalse((self.tmp / "out").exists())  # dry run writes nothing

    def test_dry_run_fullscreen_and_map_override(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            perf.main(["--dry-run", "--fullscreen", "--map", "/Game/Maps/TeddyChamberParity", "--engine-root", "C:/UE"])
        self.assertIn("-fullscreen", buffer.getvalue())
        self.assertNotIn("-windowed", buffer.getvalue())
        self.assertIn("/Game/Maps/TeddyChamberParity", buffer.getvalue())

    def test_analyze_writes_outputs(self):
        out = self.tmp / "analysis"
        with contextlib.redirect_stdout(io.StringIO()):
            code = perf.main(["--analyze", str(CSV), "--log", str(LOG), "--out", str(out), *BASE_ARGS])
        self.assertEqual(code, 0)
        for name in ("profile.csv", "engine.log", "frames.csv", "hitches.csv", "summary.json"):
            self.assertTrue((out / name).is_file(), name)
        summary = json.loads((out / "summary.json").read_text())
        self.assertEqual(summary["verdict"], "pass")
        self.assertIn("assumptions", summary)
        header = (out / "hitches.csv").read_text().splitlines()[0]
        self.assertEqual(header.split(",")[:4], ["frame", "time_s", "frame_ms", "limiter"])


if __name__ == "__main__":
    unittest.main()
