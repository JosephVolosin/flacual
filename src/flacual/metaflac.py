import subprocess
from os.path import basename
from pathlib import Path
from typing import Any

from textual import log

METAFLAC = "metaflac"


def is_metaflac_callable() -> bool:
    """Checks if metaflac is callable (i.e., in your path).

    Returns:
        True if `metaflac` was callable, otherwise False.
    """

    try:
        subprocess.run([METAFLAC], capture_output=True)
        return True
    except:
        return False


class Song:
    """Abstraction for a specific song/file."""

    def list_tags(self):
        """Retrieve all the song's tags."""

        tags_raw = subprocess.run(
            [METAFLAC, "--list", self.filepath], capture_output=True
        )
        tags = tags_raw.stdout.decode("utf-8").split("\n")
        comment_tags = [tag.split(":")[1].strip() for tag in tags if "comment[" in tag]
        comment_tags_map = {}
        for comment_tag in comment_tags:
            try:
                tag_key = comment_tag.split("=")[0].strip()
                tag_value = comment_tag.split("=")[1].strip()
                comment_tags_map[tag_key] = tag_value
            except IndexError:
                log(f"Unable to add the following tag to display: {comment_tag}")
        sorted_map = {
            key: comment_tags_map[key] for key in sorted(comment_tags_map)
        }  # Sort alphabetically for easier reading
        return sorted_map

    def set_tag(self, tag: str, value: Any) -> bool:
        """Sets a tag to a new value."""

        set_tag_payload = f"{tag}={value}"
        log(f"Updating '{tag}' to '{value}'")
        log(set_tag_payload)
        set_tag_resp = subprocess.run(
            [METAFLAC, f"--set-tag={set_tag_payload}", self.filepath],
            capture_output=True,
        )
        try:
            set_tag_resp.check_returncode()
        except subprocess.CalledProcessError:
            log(set_tag_resp.stderr)
            log(set_tag_resp.returncode)
            return False
        log(set_tag_resp.stdout)
        return True

    def remove_tag(self, tag: str) -> bool:
        """Removes the specified tag."""

        log(f"Remove '{tag}'")
        remove_tag_resp = subprocess.run(
            [METAFLAC, f"--remove-tag={tag}", self.filepath], capture_output=True
        )
        try:
            remove_tag_resp.check_returncode()
        except subprocess.CalledProcessError:
            log(remove_tag_resp.stderr)
            log(remove_tag_resp.returncode)
            return False
        log(remove_tag_resp.stdout)
        return True

    def __init__(self, filepath: str):
        if not Path(filepath).exists():
            raise FileNotFoundError(f"{filepath} does not exist. Was it moved?")
        self.filepath = filepath
        self.filename = basename(filepath)
