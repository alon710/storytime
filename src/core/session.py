from typing import Any, Literal, Optional
import threading

ArtifactType = Literal["images", "files", "texts", "available_images"]


class SessionContext:
    def __init__(self):
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._current_session = threading.local()
        self._lock = threading.Lock()

    def set_current_session(self, session_id: str):
        self._current_session.id = session_id

    def get_current_session(self) -> Optional[str]:
        return getattr(self._current_session, "id", None)

    def clear_artifacts(self, session_id: str):
        with self._lock:
            self._artifacts[session_id] = {}

    def add_artifacts(
        self,
        artifact_type: ArtifactType,
        data: Any,
        session_id: Optional[str] = None,
    ):
        if session_id is None:
            session_id = self.get_current_session()

        if session_id is None:
            return

        with self._lock:
            if session_id not in self._artifacts:
                self._artifacts[session_id] = {}

            if artifact_type not in self._artifacts[session_id]:
                self._artifacts[session_id][artifact_type] = []

            if isinstance(data, list):
                self._artifacts[session_id][artifact_type].extend(data)
            else:
                self._artifacts[session_id][artifact_type].append(data)

    def get_artifacts(self, session_id: str, artifact_type: ArtifactType) -> list[Any]:
        with self._lock:
            return self._artifacts.get(session_id, {}).get(artifact_type, [])

    def get_all_artifacts(self, session_id: str) -> dict[str, list[Any]]:
        with self._lock:
            return self._artifacts.get(session_id, {}).copy()


session_context = SessionContext()
