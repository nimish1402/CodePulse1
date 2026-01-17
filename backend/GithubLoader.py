from git import Repo
from langchain.document_loaders import GitLoader
import os
import shutil
import tempfile
from dotenv import load_dotenv

load_dotenv()


def file_filter(file_path):
    """Filter out files that don't need AI summaries"""
    
    # Directories to exclude
    exclude_dirs = [
        "node_modules/", ".git/", "dist/", "build/", "__pycache__/",
        "venv/", "env/", ".venv/", "vendor/", "target/",
        ".next/", "out/", "coverage/", ".pytest_cache/"
    ]
    
    # File patterns to exclude
    exclude_patterns = [
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "Gemfile.lock", "composer.lock", "Cargo.lock"
    ]
    
    # File extensions to exclude
    exclude_extensions = [
        # Binary/Media
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
        ".mp4", ".avi", ".mov", ".mp3", ".wav",
        ".pdf", ".zip", ".tar", ".gz", ".7z",
        
        # Documentation (already readable)
        ".md", ".txt", ".rst",
        
        # Config/Data files
        ".json", ".yaml", ".yml", ".toml", ".ini", ".xml",
        ".csv", ".tsv",
        
        # Compiled/Generated
        ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
        ".wasm", ".map",
        
        # Database
        ".db", ".sqlite", ".sqlite3"
    ]
    
    # Check directory exclusions
    for exclude_dir in exclude_dirs:
        if exclude_dir in file_path:
            return False
    
    # Check file pattern exclusions
    file_name = file_path.split("/")[-1]
    if file_name in exclude_patterns:
        return False
    
    # Check extension exclusions
    for ext in exclude_extensions:
        if file_path.endswith(ext):
            return False
    
    return True


class GithubLoader:
    def __init__(self):
        """
        this class is responsible for loading in a github repository
        """

    def load(self, url: str):
        # Use a unique temporary directory for each clone
        tmp_path = tempfile.mkdtemp(prefix="github_repo_")
        repo = Repo.clone_from(
            url,
            to_path=tmp_path,
        )
        branch = repo.head.reference

        loader = GitLoader(repo_path=tmp_path, branch=branch, file_filter=file_filter)
        return loader


# github_loader = GithubLoader()
# loader = github_loader.load("https://github.com/travisleow/codehub")
# docs = loader.load()
# for doc in docs:
#     print(doc.metadata["source"])
