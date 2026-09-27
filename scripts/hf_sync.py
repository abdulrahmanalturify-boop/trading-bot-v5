"""
scripts/hf_sync.py - Copies the site from GitHub to a Hugging Face Space after every push to main
(.github/workflows/hf-sync.yml). The Space is created on the first run, and the site's secrets are copied to it.

Needs the GitHub secret HF_TOKEN (a Hugging Face token with the "Write" role). Optional: the GitHub variable HF_SPACE
("user/name"; default "<your user>/alturaifi-pro"). Without HF_TOKEN it does nothing.
HF_DRY_RUN=1 only prepares the folder and lists it.
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = (".github/", ".devcontainer/", "research/", "tests/", "docs/", "scripts/", "deploy/")
SKIP_FILES = {"README.md", ".gitignore"}
SECRETS = ("SUPABASE_URL", "SUPABASE_KEY", "BOTS_PASSWORD", "FRED_API_KEY")   # copied to the Space when set on GitHub


def files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    return [f for f in out if f and not f.startswith(SKIP) and f not in SKIP_FILES]


def stage(dest):
    for f in files():
        os.makedirs(os.path.join(dest, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dest, f))
    for f in ("Dockerfile", "README.md"):
        shutil.copy2(os.path.join(ROOT, "deploy", "hf", f), os.path.join(dest, f))


def main():
    token = os.environ.get("HF_TOKEN", "").strip()
    dry = os.environ.get("HF_DRY_RUN") == "1"
    if not token and not dry:
        print("HF_TOKEN is not set: nothing to copy to Hugging Face.")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        stage(tmp)
        listing = sorted(os.path.relpath(os.path.join(d, f), tmp) for d, _, fs in os.walk(tmp) for f in fs)
        if dry:
            print("\n".join(listing))
            return 0
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        space = os.environ.get("HF_SPACE", "").strip() or f"{api.whoami()['name']}/alturaifi-pro"
        api.create_repo(space, repo_type="space", space_sdk="docker", private=False, exist_ok=True)
        for k in SECRETS:
            v = os.environ.get(k, "").strip()
            if v:
                api.add_space_secret(space, k, v)
        sha = os.environ.get("GITHUB_SHA", "")[:7]
        api.upload_folder(folder_path=tmp, repo_id=space, repo_type="space", delete_patterns=["*"],
                          commit_message=f"Site from GitHub {sha}".strip())
        user, name = space.split("/", 1)
        print(f"{len(listing)} files copied to https://huggingface.co/spaces/{space}")
        print(f"The site: https://{user.lower()}-{name.lower().replace('_', '-').replace('.', '-')}.hf.space")
    return 0


def report(e):
    """The error as a GitHub annotation (readable on the run's page), with anything that looks like a token hidden."""
    import re
    msg = re.sub(r"hf_[A-Za-z0-9]{6,}", "hf_***", f"{type(e).__name__}: {e}").replace("\n", " ")[:600]
    print(f"::error title=Hugging Face sync::{msg}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                  # say what went wrong where it can be read, then fail the run
        report(e)
        raise
