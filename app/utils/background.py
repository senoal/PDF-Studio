"""Small Tkinter-safe helper for long-running document operations."""

from __future__ import annotations

from collections.abc import Callable
from queue import Empty, Queue
from threading import Thread


def run_in_background(
    widget,
    task: Callable[[], object],
    on_success: Callable[[object], None],
    on_error: Callable[[Exception], None],
    on_finally: Callable[[], None] | None = None,
) -> None:
    """Run work away from Tk's event loop and marshal results back safely."""

    result_queue: Queue[tuple[str, object]] = Queue(maxsize=1)

    def poll_result() -> None:
        try:
            outcome, payload = result_queue.get_nowait()
        except Empty:
            try:
                widget.after(40, poll_result)
            except Exception:
                pass
            return

        try:
            if outcome == "success":
                on_success(payload)
            else:
                on_error(payload)
        finally:
            if on_finally is not None:
                on_finally()

    def worker() -> None:
        try:
            result = task()
        except Exception as exc:
            result_queue.put(("error", exc))
        else:
            result_queue.put(("success", result))

    Thread(target=worker, daemon=True).start()
    poll_result()
