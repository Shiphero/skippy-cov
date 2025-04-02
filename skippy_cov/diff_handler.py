from __future__ import annotations

import io
import logging
from collections import defaultdict
from pathlib import Path

from unidiff import PatchSet

logger = logging.getLogger(__name__)


class DiffHandlerError(Exception):
    pass


class DiffHandler:
    def __init__(self, contents: str):
        """
        Args:
            diff_file: The contents of the file containing the full output of a 'git diff' command.

        Raises:
            FileNotFoundError: If the specified diff file does not exist.
        """
        self.changes = self.parse_diff(contents)

    @property
    def changed_files(self) -> set[Path]:
        return set(self.changes.keys())

    def __getitem__(self, key: Path) -> str:
        return self.changes[key]

    def parse_diff(self, diff_text: str) -> defaultdict[Path, str]:
        """
        Parses the full text output of 'git diff' using the 'unidiff' library.

        Args:
            diff_text: A string containing the full output of a 'git diff' command.

        Returns:
            A set of unique file paths affected by the diff and the affected diff
        """
        mapped_changes: defaultdict[Path, str] = defaultdict(str)
        try:
            patch_set = PatchSet(io.StringIO(diff_text))

            for patched_file in patch_set:
                if patched_file.is_removed_file:
                    path = patched_file.source_file
                    if path.startswith("a/"):
                        path = path[2:]
                else:
                    path = patched_file.target_file
                    if path.startswith("b/"):
                        path = path[2:]
                mapped_changes[Path(path)] = str(patched_file).strip()
        except Exception as e:
            logger.exception("Failed to parse diff using unidiff")
            raise DiffHandlerError() from e

        return mapped_changes
