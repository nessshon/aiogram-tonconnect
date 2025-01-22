from asyncio import Task
from typing import Dict, Optional

TASKS: Dict[int, Task] = {}


class TaskStorage:
    """
    Storage for managing user-specific asynchronous tasks.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def add(self, task: Task) -> None:
        """
        Add a task to the storage.

        If a task already exists for the user, it is removed before adding the new task.

        :param task: Task to be added.
        """
        if self.user_id in TASKS:
            self.remove()
        TASKS[self.user_id] = task

    def get(self) -> Optional[Task]:
        """
        Get the task associated with the user.

        :return: Task associated with the user, or None if not found.
        """
        return TASKS.get(self.user_id)

    def remove(self) -> None:
        """
        Remove the task associated with the user.

        If the task exists and is not done, it is canceled.
        """
        task = self.get()
        if task and not task.done():
            task.cancel()
        TASKS.pop(self.user_id, None)
