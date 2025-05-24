from pathlib import Path
from repomix import RepoProcessor
import structlog

logger = structlog.get_logger()

repomix_config = Path(__file__).parent / "repomix.config.json"


def compress_repo(repo_path: str) -> str:
    """Compress a repository into a single file

    Args:
        repo_path: The path to the repository to compress

    Returns:
        The compressed repository as a string
    """

    if isinstance(repo_path, str):
        repo_path = Path(repo_path)

    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path {repo_path} does not exist")

    repo_processor = RepoProcessor(repo_path, config_path=repomix_config.as_posix())
    result = repo_processor.process(write_output=False)

    return result.output_content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", type=str, required=True)
    args = parser.parse_args()

    result = compress_repo(repo_path=args.repo_path)
    # tail 100 lines of the result
    print(result.split("\n")[-100:])
