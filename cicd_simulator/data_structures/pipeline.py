class StageNode:
    def __init__(self, name: str):
        self.name: str = name
        self.status: str = "pending"
        self.next: 'StageNode | None' = None

    def __repr__(self):
        return f"StageNode(name='{self.name}', status='{self.status}')"


class PipelineLinkedList:
    def __init__(self):
        self._head: StageNode | None = None
        self._current: StageNode | None = None

    def add_stage(self, name: str):
        new_node = StageNode(name)
        if self._head is None:
            self._head = new_node
        else:
            cursor = self._head
            while cursor.next is not None:
                cursor = cursor.next
            cursor.next = new_node

    def start(self):
        self._current = self._head
        if self._current:
            self._current.status = "in_progress"

    def advance(self, success: bool) -> bool:
        if self._current is None:
            return False
        if not success:
            self._current.status = "failed"
            return False
        self._current.status = "successful"
        if self._current.next is not None:
            self._current = self._current.next
            self._current.status = "in_progress"
            return True
        return False

    def get_all(self) -> list:
        nodes = []
        cursor = self._head
        while cursor is not None:
            nodes.append(cursor)
            cursor = cursor.next
        return nodes

    @property
    def current_stage(self) -> StageNode | None:
        return self._current