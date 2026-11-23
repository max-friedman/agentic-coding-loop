#!/usr/bin/env python3
"""prelanding.py: the gate-change and review-line rules, the fail-fast body check, and the batch run (grouping,
bisecting a red run, real merges in a scratch repository).
    python3 templates/project-kit/scripts/test_prelanding.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prelanding  # noqa: E402

CFG = {**prelanding.DEFAULTS, "code_paths": ["src/"]}
FILES = [".claude/hooks/git_rules.py", "src/app.py"]


class GateChange(unittest.TestCase):
    def test_gate_and_code_without_a_line_is_refused(self):
        why = prelanding.gate_change_refusal(FILES, "", CFG)
        self.assertIn("changes a gate (.claude/hooks/git_rules.py)", why)
        self.assertIn("Gate change: reviewed by", why)

    def test_an_independent_reviewer_passes(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES, "Body.\nGate change: reviewed by a fresh reviewer agent\n", CFG), "")
        self.assertEqual(prelanding.gate_change_refusal(FILES, "- Gate change: reviewed by the owner", CFG), "")

    def test_the_author_or_coordinator_does_not_count(self):
        for who in ("me", "the author", "Coordinator", "self (checked twice)"):
            why = prelanding.gate_change_refusal(FILES, f"Gate change: reviewed by {who}", CFG)
            self.assertIn("isn't independent", why, who)

    def test_gate_alone_or_code_alone_is_fine(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES[:1], "", CFG), "")
        self.assertEqual(prelanding.gate_change_refusal(FILES[1:], "", CFG), "")
        self.assertNotEqual(prelanding.gate_change_refusal(["scripts/deploy_gate.py", "src/x.py"], "", CFG), "")

    def test_off_without_code_paths(self):
        self.assertEqual(prelanding.gate_change_refusal(FILES, "", prelanding.DEFAULTS), "")


RULES = {**prelanding.DEFAULTS, "review_lines": [{"name": "Fidelity", "when_body": "^Cutover:", "when_paths": ["ui/"]}]}


class ReviewLines(unittest.TestCase):
    def test_a_cutover_body_without_the_line_is_refused(self):
        why = prelanding.missing_review_lines(["config/flags.json"], "Cutover: the new screen\n", RULES)
        self.assertEqual(len(why), 1)
        self.assertIn("Fidelity: OK", why[0])

    def test_a_listed_path_needs_it_too(self):
        self.assertIn("ui/home.py", prelanding.missing_review_lines(["ui/home.py"], "", RULES)[0])

    def test_an_independent_ok_passes_and_the_author_does_not(self):
        body = "Cutover: x\nFidelity: OK (fresh-reviewer, sheet 1a2b)\n"
        self.assertEqual(prelanding.missing_review_lines([], body, RULES), [])
        self.assertIn("isn't independent", prelanding.missing_review_lines([], "Cutover: x\nFidelity: OK (author)", RULES)[0])
        self.assertTrue(prelanding.missing_review_lines([], "Cutover: x\nFidelity: pending", RULES))

    def test_nothing_required_otherwise(self):
        self.assertEqual(prelanding.missing_review_lines(["src/a.py"], "A change.", RULES), [])
        self.assertEqual(prelanding.missing_review_lines(["ui/a.py"], "Cutover: x", prelanding.DEFAULTS), [])


class MainCheckout(unittest.TestCase):
    def test_a_worktree_of_a_bare_repo_reads_its_own_top_level(self):
        import os, subprocess, tempfile
        tmp = Path(tempfile.mkdtemp(prefix="prelanding-bare-"))
        run = lambda *a, cwd=tmp: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)  # noqa: E731
        run("init", "-q", "--bare", "-b", "main", "repo.git")
        run("worktree", "add", "-q", "--orphan", "-b", "main", str(tmp / "wt"), cwd=tmp / "repo.git")
        old = os.getcwd()
        os.chdir(tmp / "wt")
        try:
            self.assertEqual(prelanding.main_checkout(), (tmp / "wt").resolve())
        finally:
            os.chdir(old)

    def test_cut_configured(self):
        import json, tempfile
        d = Path(tempfile.mkdtemp())
        self.assertFalse(prelanding.cut_configured(str(d)))
        (d / ".loop").mkdir()
        (d / ".loop" / "config.json").write_text(json.dumps({"cutover": {"passes_file": "x"}}))
        self.assertTrue(prelanding.cut_configured(str(d)))


class FailFast(unittest.TestCase):
    def test_every_body_problem_is_reported_at_once(self):
        body = "- Intentional revert: x\nFidelity: OK (author)\n"
        got = prelanding.body_problems(FILES + ["ui/a.py"], body, {**RULES, "code_paths": ["src/"]})
        self.assertEqual(sorted(c for c, _ in got), [11, 13, 13], got)
        self.assertTrue(any("Intentional revert" in w for _, w in got))
        self.assertTrue(any("isn't independent" in w for _, w in got))

    def test_a_missing_review_line_is_not_a_fail_fast_problem(self):
        self.assertEqual(prelanding.body_problems(["ui/a.py"], "A change.", RULES), [])
        self.assertTrue(prelanding.missing_review_lines(["ui/a.py"], "A change.", RULES), "…it is still refused after the checks")

    def test_a_plain_revert_line_and_prose_pass(self):
        self.assertEqual(prelanding.revert_line_problem("Intentional revert: put the old text back"), "")
        self.assertEqual(prelanding.revert_line_problem("This is not an intentional revert of anything."), "")
        self.assertIn("plain line", prelanding.revert_line_problem("> **Intentional revert:** x"))

    def test_body_only_reads_a_body_file(self):
        import subprocess, tempfile
        body = Path(tempfile.mkdtemp()) / "body.md"
        body.write_text("* Intentional revert: x\n")
        r = subprocess.run([sys.executable, prelanding.__file__, "--body-only", "--body", str(body)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 13, r.stdout + r.stderr)
        self.assertIn("plain line", r.stdout)
        body.write_text("Fine.\n")
        r = subprocess.run([sys.executable, prelanding.__file__, "--body-only", "--body", str(body)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


def pr(n, files=(), **kw):
    return {"pr": n, "head": f"h{n}", "files": list(files), "body": "", **kw}


class Batch(unittest.TestCase):
    def test_groups_cap_the_run_and_alone_ones_go_last(self):
        ms = [pr(i) for i in range(1, 6)] + [pr(9, alone="a gate")]
        runs = prelanding.batch_groups(ms[:3] + [pr(9, alone="a gate")] + ms[3:5], 2)
        self.assertEqual([[m["pr"] for m in r] for r in runs], [[1, 2], [3, 4], [5], [9]])

    def test_alone_paths_and_gates(self):
        cfg = {**prelanding.DEFAULTS, "alone_paths": ["db/migrations/"]}
        self.assertIn("a gate", prelanding.batch_alone(["scripts/prelanding.py"], cfg))
        self.assertIn("lands alone", prelanding.batch_alone(["db/migrations/1.sql"], cfg))
        self.assertEqual(prelanding.batch_alone(["src/a.py"], cfg), "")

    def settle(self, group, bad=(), env=(), conflict=()):
        runs = []

        def check(g):
            prs = [m["pr"] for m in g]
            runs.append(prs)
            if any(p in conflict for p in prs):
                return {"ok": False, "conflict": next(p for p in prs if p in conflict), "why": "conflict"}
            if any(p in env for p in prs):
                return {"ok": False, "env": True, "why": "ENVIRONMENT"}
            return {"ok": not any(p in bad for p in prs), "why": "checks failed", "tree": "t" + "".join(map(str, prs))}
        return prelanding.settle(group, check, say=lambda _m: None), runs

    def test_green_run_passes_everyone_in_one_run(self):
        got, runs = self.settle([pr(1), pr(2), pr(3)])
        self.assertEqual(runs, [[1, 2, 3]])
        self.assertTrue(all(r["outcome"] == "passed" and r["run"] == [1, 2, 3] for r in got.values()))

    def test_red_run_is_bisected_to_the_culprit(self):
        got, runs = self.settle([pr(1), pr(2), pr(3), pr(4)], bad=(3,))
        self.assertEqual({k: v["outcome"] for k, v in got.items()}, {1: "passed", 2: "passed", 3: "failed", 4: "passed"})
        self.assertEqual(got[3]["culprit_of"], [1, 2, 3, 4])
        self.assertEqual(runs, [[1, 2, 3, 4], [1, 2], [3, 4], [3], [4]])

    def test_an_environment_failure_blames_nobody(self):
        got, runs = self.settle([pr(1), pr(2)], env=(1,))
        self.assertEqual(runs, [[1, 2]])
        self.assertTrue(all(r["outcome"] == "failed" and "culprit_of" not in r for r in got.values()))

    def test_a_conflicting_member_runs_on_its_own(self):
        got, runs = self.settle([pr(1), pr(2), pr(3)], conflict=(2,))
        self.assertEqual(got[2]["outcome"], "conflict")
        self.assertEqual((got[1]["outcome"], got[3]["outcome"]), ("passed", "passed"))

    def test_run_batch_refuses_covers_and_records(self):
        import tempfile
        recorded, cfg = [], {**prelanding.DEFAULTS, "gate_paths": ["ci/"]}
        members = {1: pr(1, ["a.py"]), 2: pr(2, ["a.py"]), 3: pr(3, ["ci/x.yml"]), 4: pr(4)}
        refuse = lambda m: (13, "needs a review line") if m["pr"] == 2 else (0, "")  # noqa: E731
        old, rd = prelanding.record_dir, Path(tempfile.mkdtemp())
        prelanding.record_dir = lambda: rd
        (rd / "h4").write_text("")  # PR 4's head already has a pass
        try:
            got = prelanding.run_batch(Path("."), [1, 2, 3, 4, 3], "origin/main", cfg, ["true"], ".",
                                       member_fn=lambda n: members[n], refusal_fn=refuse,
                                       check_fn=lambda g: {"ok": True, "tree": "T"}, record_fn=lambda *a: recorded.append(a),
                                       plan_only=False)
        finally:
            prelanding.record_dir = old
        self.assertEqual({k: v["outcome"] for k, v in got.items()}, {1: "passed", 2: "refused", 3: "passed", 4: "covered"})
        self.assertEqual(got[2]["code"], 13)
        self.assertEqual(sorted(a[0] for a in recorded), ["h1", "h3"])
        self.assertEqual(got[1]["run"], [1], "the gate-changing PR 3 ran alone, so 1 is by itself too")


class RealGit(unittest.TestCase):
    """check_group merges real heads onto main in a throwaway worktree, runs the checks once, and cleans up."""

    def setUp(self):
        import os, subprocess, tempfile
        self._t = tempfile.TemporaryDirectory()
        self.d = Path(os.path.realpath(self._t.name))
        self.repo = self.d / "repo"
        self.repo.mkdir()
        self.old = os.getcwd()
        self.g("init", "-q", "-b", "main")
        for k, v in {"user.name": "t", "user.email": "t@example.invalid", "commit.gpgsign": "false"}.items():
            self.g("config", k, v)
        (self.repo / "shared.txt").write_text("one\n")
        self.commit("init")
        os.chdir(self.repo)

    def tearDown(self):
        import os
        os.chdir(self.old)
        self._t.cleanup()

    def g(self, *a):
        import subprocess
        return subprocess.run(["git", *a], cwd=self.repo, capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, msg):
        self.g("add", "-A")
        self.g("commit", "-qm", msg)

    def branch(self, name, **files):
        self.g("checkout", "-q", "-b", name, "main")
        for f, text in files.items():
            (self.repo / f.replace("_", ".")).write_text(text)
        self.commit(name)
        head = self.g("rev-parse", "HEAD")
        self.g("checkout", "-q", "main")
        return {"pr": int(name[1:]), "head": head, "branch": name, "files": [], "body": ""}

    def test_green_red_and_conflict(self):
        cfg = prelanding.knobs(str(self.repo))
        a, b = self.branch("p1", a_txt="a\n"), self.branch("p2", b_txt="b\n")
        c = self.branch("p3", shared_txt="three\n")
        d = self.branch("p4", shared_txt="four\n")
        run = lambda g, cmds: prelanding.check_group(self.repo, g, "main", cmds, cfg)  # noqa: E731
        got = run([a, b], ["test -f a.txt && test -f b.txt"])
        self.assertTrue(got["ok"] and got["tree"], got)
        got = run([a, b], ["test -f c.txt"])
        self.assertFalse(got["ok"] or got.get("env"), got)
        got = run([c, d], ["true"])
        self.assertEqual(got.get("conflict"), 4, got)
        self.assertIn("shared.txt", got["why"])
        self.assertEqual(self.g("worktree", "list").count("\n"), 0, "every throwaway worktree is gone")
        marked = prelanding.check_group(self.repo, [a], "main", ["echo ENVIRONMENT, not your PR; false"], cfg)
        self.assertTrue(marked["env"] and not marked["ok"])
        # the whole path: bisect names the failing PR only
        bad = lambda g: run(g, ["test ! -f b.txt"])  # noqa: E731
        out = prelanding.settle([a, b, c], bad, say=lambda _m: None)
        self.assertEqual({k: v["outcome"] for k, v in out.items()}, {1: "passed", 2: "failed", 3: "passed"})


if __name__ == "__main__":
    unittest.main()
