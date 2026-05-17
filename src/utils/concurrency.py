import traceback
import sys
from typing import Callable, Any
from PySide6.QtCore import QRunnable, QObject, Signal, Slot

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)


class Worker(QRunnable):
    """
    Worker thread for running tasks in the background.
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up.
    """
    def __init__(self, fn: Callable, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        """
        Executes the function with provided arguments.
        Emits signals on error, completion, and result.
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            exctype, value, tb = sys.exc_info()
            if exctype and value:
                error_msg = traceback.format_exc()
                print(f"Worker Error: {error_msg}")
                self.signals.error.emit((exctype, value, error_msg))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
