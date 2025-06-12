import concurrent.futures
import os
import shutil
import stat
import subprocess
import sys
import time

from dotenv import load_dotenv

# Ensure the output directory exists, configurable via .env (OUTPUT_DIR), defaults to 'repomixd'
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "repomixd")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def remove_git_dir(git_dir: str, max_retries: int = 3, delay: float = 1.0) -> bool:
    """
    Attempt to robustly remove a .git directory, with retries and permission fixes for Windows.
    Args:
        git_dir: Path to the .git directory.
        max_retries: Number of attempts before giving up.
        delay: Seconds to wait between retries.
    Returns:
        True if successfully removed or not present, False otherwise.
    """

    def on_rm_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            print(f"[WARN] Could not forcibly remove {path}: {str(exc_info[1])}")

    for attempt in range(max_retries):
        try:
            if os.path.isdir(git_dir):
                shutil.rmtree(git_dir, onexc=on_rm_error)
                print(f"[INFO] Successfully removed .git directory: {git_dir}")
            else:
                print(f"[INFO] No .git directory found at {git_dir} (already clean)")
            return True
        except Exception as e:
            print(
                f"[WARN] Attempt {attempt + 1}: Failed to remove .git directory {git_dir}: {e}"
            )
            time.sleep(delay)
    print(
        f"[ERROR] Could not remove .git directory after {max_retries} attempts: {git_dir}"
    )
    return False


load_dotenv()


def process_repo(repo_input: str) -> None:
    """
    Process a single repository.

    Args:
        repo_input: The input string from the command line or source file, e.g. "bitcoin/bitcoin".

    Environment Variables:
        GH_TOKEN: If set, use the GitHub CLI to clone the repository instead of git.
        OUTPUT_DIR: Directory to write repomix output files to, defaults to "repomixd".

    Returns:
        None
    """
    repo_url = f"https://github.com/{repo_input}"
    repo_name = repo_input.split("/")[-1]
    output_dir = os.environ.get("OUTPUT_DIR", "repomixd")
    os.makedirs(output_dir, exist_ok=True)

    # Always use absolute path for repo directory
    repo_dir = os.path.abspath(repo_name)
    if os.path.exists(repo_dir):
        try:
            shutil.rmtree(repo_dir)
        except Exception as e:
            print(
                f"[WARN] Could not remove pre-existing repo directory {repo_dir}: {e}"
            )

    try:
        # Clone
        if os.environ.get("GH_TOKEN"):
            subprocess.run(["gh", "repo", "clone", repo_url], check=True)
        else:
            subprocess.run(["git", "clone", repo_url], check=True)
        # Remove .git directory to avoid leaving git metadata
        git_dir = os.path.join(repo_name, ".git")
        remove_git_dir(git_dir)

        # Find the output file
        import shutil as _shutil

        npx_path = _shutil.which("npx")
        if not npx_path:
            print(
                "npx not found in PATH! Please install Node.js and ensure npx is available."
            )
            return
        subprocess.run(
            [
                npx_path,
                "repomix",
                "--ignore",
                "**/*.a,**/*.accdb,**/*.ai,**/*.aac,**/*.bin,**/*.bmp,**/*.bak,**/*.backup,**/*.bundle.js,**/*.bundle.css,**/*.cache,**/*.class,**/*.csv,**/*.db,**/*.dex,**/*.dll,**/*.doc,**/*.docx,**/*.ear,**/*.eot,**/*.eps,**/*.exe,**/*.fig,**/*.flac,**/*.gif,**/*.gz,**/*.ico,**/*.ics,**/*.jar,**/*.jpeg,**/*.jpg,**/*.map,**/*.m4a,**/*.mdb,**/*.md,**/*.mkv,**/*.mov,**/*.mp3,**/*.mp4,**/*.obj,**/*.o,**/*.orig,**/*.otf,**/*.pdf,**/*.pyd,**/*.pyo,**/*.pyc,**/*.ppt,**/*.pptx,**/*.psd,**/*.rbc,**/*.rar,**/*.swp,**/*.swo,**/*.sql,**/*.svg,**/*.tar,**/*.tgz,**/*.tmp,**/*.tsv,**/*.ttf,**/*.txt,**/*.unitypackage,**/*.woff,**/*.woff2,**/*.war,**/*.webm,**/*.webp,**/*.xls,**/*.xlsx,**/*.yaml,**/*.yml,**/*.zip,**/*~,**/.DS_Store,**/.git/**,**/.idea/**,**/.pytest_cache/**,**/.coverage,**/.eslintcache,**/.stylelintcache,**/.nyc_output/**,**/.awcache/**,**/.terraform/**,**/.next/**,**/.vscode/**,**/__pycache__/**,**/bower_components/**,**/build/**,**/coverage/**,**/dist/**,**/env/**,**/logs/**,**/node_modules/**,**/public/build/**,**/vendor/**,**/venv/**,**/out/**,**/test-results/**,**/jest-cache/**",
                "--verbose",
            ],
            cwd=repo_name,
            input="y\n",
            text=True,
            check=True,
        )
        repomix_out = os.path.join(repo_name, "repomix-output.xml")
        if not os.path.exists(repomix_out):
            print(f"ERROR: repomix-output.xml not found for {repo_input}")
            return
        dest = os.path.join(output_dir, f"{repo_name}_repomix.xml")
        shutil.move(repomix_out, dest)
        print(f"OK: {repo_input} -> {dest}")
    except Exception as e:
        print(f"FAIL: {repo_input}: {e}")
    finally:
        repo_dir = os.path.abspath(repo_name)
        if os.path.exists(repo_dir):
            try:
                shutil.rmtree(repo_dir)
            except Exception as e:
                print(f"[WARN] Could not remove cloned repo directory {repo_dir}: {e}")


def main() -> None:
    source_file = os.getenv("SOURCE_REPOS_TXT_FILE")

    if len(sys.argv) > 1:
        repos = [repo.strip() for repo in sys.argv[1:] if repo.strip()]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(process_repo, repos)
        for repo in repos:
            repo_name = repo.split("/")[-1]
            repo_dir = os.path.abspath(repo_name)
            try:
                if os.path.isdir(repo_dir):
                    shutil.rmtree(repo_dir)
            except Exception as e:
                print(f"[WARN] Failed to remove repo directory {repo_dir}: {e}")
    elif source_file and os.path.exists(source_file):
        with open(source_file, "r", encoding="utf-8") as f:
            repos = [line.strip() for line in f if line.strip()]
        if repos:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_repo, repos)
        else:
            print("No repositories found in the source file.")
    else:
        print("Usage: python script.py [repository1 repository2 ...]")
        print(
            "Or set SOURCE_REPOS_TXT_FILE environment variable to a file containing list of repositories."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
