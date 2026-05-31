#!/usr/bin/env python3
"""恢复被损坏的 daily-news repo - 一次性重建所有文件"""
import os, json, base64, urllib.request, sys

TOKEN = os.environ.get("GH_TOKEN", "")
BASE = "https://api.github.com/repos/Tffdbb/daily-news"

LOCAL_DIR = r"G:\claw1232\portable\data\.openclaw\canvas\daily-news"

def gh(method, path, body=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json"
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

print("Step 1: Get current ref")
ref = gh("GET", "/git/ref/heads/main")
base_sha = ref["object"]["sha"]
print(f"  Base: {base_sha}")

print("Step 2: Create blobs for all scripts")
all_files = {
    ".github/scripts/fetch_news.py":      os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_news.py"),
    ".github/scripts/fetch_rss.py":       os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_rss.py"),
    ".github/scripts/fetch_more.py":      os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_more.py"),
    ".github/scripts/fetch_shop.py":      os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_shop.py"),
    ".github/scripts/fetch_metal_vol.py": os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_metal_vol.py"),
    ".github/scripts/fetch_quant.py":     os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_quant.py"),
    ".github/scripts/fetch_trending.py":  os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_trending.py"),
    ".github/scripts/fetch_crypto.py":    os.path.join(LOCAL_DIR, ".github", "scripts", "fetch_crypto.py"),
    ".github/scripts/merge_news.py":      os.path.join(LOCAL_DIR, ".github", "scripts", "merge_news.py"),
    ".github/scripts/generate_site.py":   os.path.join(LOCAL_DIR, ".github", "scripts", "generate_site.py"),
    ".github/scripts/enhance_news.py":    os.path.join(LOCAL_DIR, ".github", "scripts", "enhance_news.py"),
    ".github/scripts/track_quant.py":     os.path.join(LOCAL_DIR, ".github", "scripts", "track_quant.py"),
    ".github/workflows/daily-news.yml":   os.path.join(LOCAL_DIR, ".github", "workflows", "daily-news.yml"),
}

blobs = {}
for remote, local in all_files.items():
    with open(local, "rb") as f:
        content = f.read()
    blob = gh("POST", "/git/blobs", {"content": content.decode("utf-8"), "encoding": "utf-8"})
    blobs[remote] = blob["sha"]
    print(f"  {remote}: {blob['sha'][:12]}")

print("\nStep 3: Create tree")
tree_items = []
for remote, sha in blobs.items():
    tree_items.append({"path": remote, "mode": "100644", "type": "blob", "sha": sha})

# Also keep the existing root-level files
cur_tree = gh("GET", f"/git/trees/{base_sha}")
for entry in cur_tree["tree"]:
    if entry["path"] in [".nojekyll", "README.md", "index.html"]:
        tree_items.append({"path": entry["path"], "mode": entry["mode"], "type": entry["type"], "sha": entry["sha"]})
        print(f"  (keep) {entry['path']}: {entry['sha'][:12]}")

tree_body = {"base_tree": base_sha, "tree": tree_items}
new_tree = gh("POST", "/git/trees", tree_body)
tree_sha = new_tree["sha"]
print(f"  New tree: {tree_sha[:12]} ({len(tree_items)} items)")

print("\nStep 4: Create commit")
commit = gh("POST", "/git/commits", {
    "message": "recovery: rebuild all scripts + add crypto section",
    "tree": tree_sha,
    "parents": [base_sha]
})
commit_sha = commit["sha"]
print(f"  Commit: {commit_sha[:12]}")

print("\nStep 5: Update ref")
gh("PATCH", "/git/refs/heads/main", {"sha": commit_sha, "force": False})
print("  Ref updated!")

print("\nStep 6: Trigger workflow")
gh("POST", "/actions/workflows/daily-news.yml/dispatches", {"ref": "main"})
print("  Workflow triggered!")

print("\nDONE")
