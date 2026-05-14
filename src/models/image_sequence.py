from typing import List, Optional
from src.models.frame_container import FrameContainer
from src.models.sequence_item import SequenceItem

class ImageSequence:
    """
    Manages a sequence of images (e.g., a folder or a diptych).
    Stores SequenceItems and manages the active FrameContainer.
    """
    def __init__(self) -> None:
        self.items: List[SequenceItem] = []
        self.active_index: int = -1
        self.active_container: Optional[FrameContainer] = None

    def set_files(self, file_paths: List[str]) -> None:
        """
        Sets the list of files, creating a SequenceItem for each, and resets the active state.
        """
        self.items = [SequenceItem(path) for path in file_paths]
        self.active_index = -1
        self.active_container = None

    def get_item_at(self, index: int) -> Optional[SequenceItem]:
        """
        Returns the SequenceItem at the given index.
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def set_active(self, index: int, container: FrameContainer) -> None:
        """
        Sets the active container at the specified index.
        """
        self.active_index = index
        self.active_container = container

