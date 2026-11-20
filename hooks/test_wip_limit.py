#!/usr/bin/env python3
"""wip_limit.py with a fake gh (LOOP_GH_BIN) and a throwaway repo: `gh pr create` is blocked at the limit of open
product PRs; drafts, non-product PRs and exempt branches go through; gh is cached; errors fail open.
    python3 hooks/test_wip_limit.py (or .claude/hooks/ once installed)"""

import json, os, subprocess as sp, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wip_limit  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ("" if ok else f"  -- {detail}"))
    if not ok:
        fails.append(name)


root = tempfile.mkdtemp(prefix="wip-hook-")
origin, repo = os.path.join(root, "origin.git"), os.path.join(root, "repo")
git = lambda *a: sp.run(["git", *a], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
sp.run(["git", "init", "-q", "--bare", origin], check=True)
sp.run(["git", "clone", "-q", origin, repo], check=True, capture_output=True)
for k, v in {"user.name": "t", "user.email": "t@example.com", "commit.gpgsign": "false"}.items():
    git("config", k, v)
open(os.path.join(repo, "README.md"), "w").write("x\n")
git("add", "-A"); git("commit", "-qm", "init"); git("push", "-q", "origin", "HEAD:main"); git("fetch", "-q")


def branch(name, path):
    git("checkout", "-q", "-B", name, "origin/main")
    os.makedirs(os.path.dirname(os.path.join(repo, path)), exist_ok=True)
    open(os.path.join(repo, path), "w").write(name + "\n")
    git("add", "-A"); git("commit", "-qm", name)


fake = os.path.join(root, "fake_gh.py")
open(fake, "w").write(f"""#!/usr/bin/env python3
import json, os, sys
open({os.path.join(root, 'gh.log')!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')
if os.environ.get('FAKE_GH_FAIL'):
    print('gh: network down', file=sys.stderr); sys.exit(1)
print(open({os.path.join(root, 'prs.json')!r}).read())
""")
os.chmod(fake, 0o755)
cache = os.path.join(root, "cache.json")
proj = os.path.join(root, "proj")
os.makedirs(os.path.join(proj, ".loop"))
ENV = {**os.environ, "LOOP_GH_BIN": fake, "WIP_LIMIT_CACHE": cache, "CLAUDE_PROJECT_DIR": proj, "WIP_LIMIT": "3"}
ENV.pop("LOOP_CONFIG", None)


def pr(n, br, files, draft=False):
    return {"number": n, "title": f"PR {n}", "headRefName": br, "isDraft": draft, "files": [{"path": f} for f in files]}


def set_prs(prs):
    json.dump(prs, open(os.path.join(root, "prs.json"), "w"))
    if os.path.exists(cache):
        os.remove(cache)


def hook(cmd, env=None):
    t = time.time()
    r = sp.run([sys.executable, os.path.join(HERE, "wip_limit.py")], capture_output=True, text=True, env={**ENV, **(env or {})},
               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": repo}))
    return r, time.time() - t


gh_calls = lambda: len(open(os.path.join(root, "gh.log")).read().splitlines()) if os.path.exists(os.path.join(root, "gh.log")) else 0  # noqa: E731
three = [pr(1, "feat-a", ["src/a.py"]), pr(2, "feat-b", ["lib/b.py", "docs/x.md"]), pr(3, "feat-c", ["src/c.py"])]

print("wip_limit.py: product paths")
D = wip_limit._loop.DEFAULTS["wip_limit"]
check("src/ counts", wip_limit.product(["src/a.py"], D))
check("docs/, tests/ and *.md don't", not wip_limit.product(["docs/a.txt", "tests/t.py", "NOTES.md"], D))
check("product_paths narrows it", not wip_limit.product(["scripts/x.py"], {**D, "product_paths": ["src/"]})
      and wip_limit.product(["src/x.py"], {**D, "product_paths": ["src/"]}))

print("wip_limit.py: the limit")
branch("feat-new", "src/new.py")
set_prs(three)
r, dt = hook("gh pr create --fill")
check("3 open product PRs: blocked (exit 2), lists them", r.returncode == 2 and "#1" in r.stderr and "limit is 3" in r.stderr, r.stderr)
check(f"fast enough: {dt * 1000:.0f} ms (< 3 s)", dt < 3, dt)
r, _ = hook("gh pr create --draft --fill")
check("a draft goes through", r.returncode == 0, r.stderr)
r, _ = hook("cd . && gh pr create --fill", env={"WIP_LIMIT": "4"})
check("under the limit: goes through", r.returncode == 0, r.stderr)
set_prs(three[:2] + [pr(3, "feat-c", ["src/c.py"], draft=True)])
r, _ = hook("gh pr create --fill")
check("drafts aren't counted", r.returncode == 0, r.stderr)
set_prs(three[:2] + [pr(3, "docs-c", ["docs/c.md"])])
r, _ = hook("gh pr create --fill")
check("docs-only PRs aren't counted", r.returncode == 0, r.stderr)
set_prs(three[:2] + [pr(3, "revert-9", ["src/c.py"])])
r, _ = hook("gh pr create --fill")
check("exempt branches aren't counted", r.returncode == 0, r.stderr)
set_prs(three)
branch("docs-only", "docs/guide.txt")
r, _ = hook("gh pr create --fill")
check("a docs-only branch goes through at the limit", r.returncode == 0, r.stderr)
branch("revert-12", "src/new.py")
r, _ = hook("gh pr create --fill")
check("a revert- branch goes through at the limit", r.returncode == 0, r.stderr)
git("checkout", "-q", "feat-new")
json.dump({"wip_limit": {"max_open_prs": 0}}, open(os.path.join(proj, ".loop", "config.json"), "w"))
r, _ = hook("gh pr create --fill", env={"WIP_LIMIT": ""})
check("max_open_prs 0: off", r.returncode == 0, r.stderr)
os.remove(os.path.join(proj, ".loop", "config.json"))

print("wip_limit.py: cache and errors")
set_prs(three)
n = gh_calls()
hook("gh pr create --fill"); hook("gh pr create --fill")
check("gh is called once within the cache window", gh_calls() - n == 1, gh_calls() - n)
os.remove(cache)
r, _ = hook("gh pr create --fill", env={"FAKE_GH_FAIL": "1"})
check("gh fails: fails open (exit 1, not 2)", r.returncode == 1 and "hook error" in r.stderr, (r.returncode, r.stderr))
r, _ = hook("gh pr list")
check("other gh commands: exit 0", r.returncode == 0 and not r.stderr, r.stderr)
r = sp.run([sys.executable, os.path.join(HERE, "wip_limit.py")], input="{", capture_output=True, text=True, env=ENV)
check("broken input: fails open (exit 1)", r.returncode == 1, r.returncode)

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all passed'}")
sys.exit(1 if fails else 0)
