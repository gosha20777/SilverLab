from typing import List, Optional
from src.models.frame_container import FrameContainer

class ImageSequence:
    """
    Manages a sequence of images (e.g., a folder or a diptych).
    Stores file paths and manages the active FrameContainer.
    """
    def __init__(self) -> None:
        self.file_paths: List[str] = []
        self.active_index: int = -1
        self.active_container: Optional[FrameContainer] = None

    def set_files(self, file_paths: List[str]) -> None:
        """
        Sets the list of files and resets the active state.
        """
        self.file_paths = file_paths
        self.active_index = -1
        self.active_container = None

    def get_file_at(self, index: int) -> Optional[str]:
        """
        Returns the file path at the given index.
        """
        if 0 <= index < len(self.file_paths):
            return self.file_paths[index]
        return None

    def set_active(self, index: int, container: FrameContainer) -> None:
        """
        Sets the active container at the specified index.
        """
        self.active_index = index
        self.active_container = container
