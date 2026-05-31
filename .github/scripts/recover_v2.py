#!/usr/bin/env python3
"""终极恢复：一次性重建 daily-news 仓库，使用嵌套树结构"""
import json, urllib.request, base64, os, sys

TOKEN = os.environ.get("GH_TOKEN", "")
BASE = "https://api.github.com/repos/Tffdbb/daily-news"
SRC = r"G:\claw1232\portable\data\.openclaw\canvas\daily-news"
CTX = None

try:
    import ssl
    CTX = ssl.create_default_context()
    CTX.check_hostname = False
    CTX.verify_mode = ssl.CERT_NONE
except:
    pass

def gh(method, path, body=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "recovery-script/1.0"
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  HTTP {e.code}: {err[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

# Step 1: get latest ref
print("=== Step 1: Get latest ref ===")
ref = gh("GET", "/git/ref/heads/main")
base_sha = ref["object"]["sha"]
print(f"  Base: {base_sha}")

# Step 2: Create blobs for all script files
print("\n=== Step 2: Create blobs ===")
blobs = {}

all_files = {
    ".github/scripts/fetch_news.py": "fetch_news.py",
    ".github/scripts/fetch_rss.py": "fetch_rss.py",
    ".github/scripts/fetch_more.py": "fetch_more.py",
    ".github/scripts/fetch_shop.py": "fetch_shop.py",
    ".github/scripts/fetch_metal_vol.py": "fetch_metal_vol.py",
    ".github/scripts/fetch_quant.py": "fetch_quant.py",
    ".github/scripts/fetch_trending.py": "fetch_trending.py",
    ".github/scripts/fetch_crypto.py": "fetch_crypto.py",
    ".github/scripts/merge_news.py": "merge_news.py",
    ".github/scripts/generate_site.py": "generate_site.py",
    ".github/scripts/enhance_news.py": "enhance_news.py",
    ".github/scripts/track_quant.py": "track_quant.py",
    ".github/workflows/daily-news.yml": os.path.join("workflows", "daily-news.yml"),
}

for remote, local in all_files.items():
    with open(os.path.join(SRC, ".github", "scripts" if local.startswith("workflows") else "scripts", 
              local if local.startswith("workflows") else local), "rb") as f:
        content = f.read()
    blob = gh("POST", "/git/blobs", {"content": base64.b64encode(content).decode(), "encoding": "base64"})
    blobs[remote] = blob["sha"]
    print(f"  {remote}: {blob['sha'][:12]}")

# Root files
root_files = {".nojekyll": "", "README.md": "# Daily News\n", "index.html": ""}
# Get index.html content
index_path = os.path.join(SRC, "index.html")
if os.path.exists(index_path):
    with open(index_path, "rb") as f:
        root_files["index.html"] = f.read().decode("utf-8")

# Also generate a simple index.html if needed
if not root_files["index.html"] or len(root_files["index.html"]) < 10:
    root_files["index.html"] = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Daily News</title><meta http-equiv='refresh' content='0;url=/'></head><body>Redirecting...</body></html>"

for name, content in root_files.items():
    b64_content = base64.b64encode(content.encode("utf-8")).decode()
    blob = gh("POST", "/git/blobs", {"content": b64_content, "encoding": "base64"})
    blobs[name] = blob["sha"]
    print(f"  {name}: {blob['sha'][:12]}")

# Step 3: Build nested trees
print("\n=== Step 3: Build nested trees ===")

# First, build .github/scripts tree
scripts_tree_items = []
for fname in ["fetch_news.py","fetch_rss.py","fetch_more.py","fetch_shop.py",
              "fetch_metal_vol.py","fetch_quant.py","fetch_trending.py",
              "fetch_crypto.py","merge_news.py","generate_site.py",
              "enhance_news.py","track_quant.py"]:
    path = f".github/scripts/{fname}"
    scripts_tree_items.append({"path": fname, "mode": "100644", "type": "blob", "sha": blobs[path]})
    print(f"  .github/scripts/: {fname}")

scripts_tree = gh("POST", "/git/trees", {"tree": scripts_tree_items})
scripts_sha = scripts_tree["sha"]
print(f"  scripts tree: {scripts_sha[:12]} ({len(scripts_tree_items)} items)")

# Build .github/workflows tree
wf_items = [{"path": "daily-news.yml", "mode": "100644", "type": "blob", "sha": blobs[".github/workflows/daily-news.yml"]}]
wf_tree = gh("POST", "/git/trees", {"tree": wf_items})
wf_sha = wf_tree["sha"]
print(f"  workflows tree: {wf_sha[:12]} ({len(wf_items)} item)")

# Build .github tree
gh_items = [
    {"path": "scripts", "mode": "040000", "type": "tree", "sha": scripts_sha},
    {"path": "workflows", "mode": "040000", "type": "tree", "sha": wf_sha},
]
gh_tree = gh("POST", "/git/trees", {"tree": gh_items})
gh_sha = gh_tree["sha"]
print(f"  .github tree: {gh_sha[:12]} ({len(gh_items)} items)")

# Build root tree
root_items = [
    {"path": ".github", "mode": "040000", "type": "tree", "sha": gh_sha},
    {"path": ".nojekyll", "mode": "100644", "type": "blob", "sha": blobs[".nojekyll"]},
    {"path": "README.md", "mode": "100644", "type": "blob", "sha": blobs["README.md"]},
    {"path": "index.html", "mode": "100644", "type": "blob", "sha": blobs["index.html"]},
]
root_tree = gh("POST", "/git/trees", {"tree": root_items})
root_sha = root_tree["sha"]
print(f"  root tree: {root_sha[:12]} ({len(root_items)} items)")

# Step 4: Create commit
print("\n=== Step 4: Create commit ===")
commit = gh("POST", "/git/commits", {
    "message": "rebuild: all scripts + crypto section (nested trees)",
    "tree": root_sha,
    "parents": [base_sha]
})
commit_sha = commit["sha"]
print(f"  Commit: {commit_sha[:12]}")

# Step 5: Update ref
print("\n=== Step 5: Update ref ===")
gh("PATCH", "/git/refs/heads/main", {"sha": commit_sha, "force": False})
print("  Ref updated!")

# Step 6: Verify
print("\n=== Step 6: Verify ===")
tree_check = gh("GET", f"/git/trees/{commit_sha}?recursive=1")
print(f"  Tree has {len(tree_check['tree'])} entries:")
for e in tree_check["tree"]:
    print(f"  {e['sha'][:8]} {e['type']:4} {e['path']}")

# Step 7: Trigger workflow
print("\n=== Step 7: Trigger workflow ===")
gh("POST", "/actions/workflows/daily-news.yml/dispatches", {"ref": "main"})
print("  Triggered!")

print("\n=== DONE ===")
