import sqlite3
import json
import threading
from typing import Any, Optional
from datetime import datetime
from core.logger import logger
from schemas.workflow import WorkflowState, WorkflowStep


class WorkflowStateManager:
    """Thread-safe manager for workflow state persistence.

    Handles storing and retrieving workflow state for each session using SQLite.
    All state is serialized to JSON for storage and deserialized on retrieval.
    """

    def __init__(self, db_path: str = "chat.db"):
        """Initialize the workflow state manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._initialize_database()
        logger.info("WorkflowStateManager initialized", db_path=db_path)

    def _initialize_database(self):
        """Create the workflow_state table if it doesn't exist."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workflow_state (
                        session_id TEXT PRIMARY KEY,
                        current_step TEXT NOT NULL,
                        challenge_data TEXT,
                        seed_image_path TEXT,
                        book_content TEXT,
                        illustrations TEXT,
                        pdf_path TEXT,
                        approvals TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )
                conn.commit()
                logger.info("Workflow state table initialized")
            except Exception as e:
                logger.error("Failed to initialize workflow state table", error=str(e))
                raise
            finally:
                conn.close()

    def _serialize_state(self, state: WorkflowState) -> dict[str, Any]:
        """Serialize WorkflowState to dictionary for database storage.

        Converts Path objects to strings and complex objects to JSON.
        """
        state_dict = state.model_dump(mode="json")

        # Convert Path objects to strings
        if state_dict.get("seed_image_path"):
            state_dict["seed_image_path"] = str(state_dict["seed_image_path"])
        if state_dict.get("pdf_path"):
            state_dict["pdf_path"] = str(state_dict["pdf_path"])
        if state_dict.get("illustrations"):
            state_dict["illustrations"] = {str(k): str(v) for k, v in state_dict["illustrations"].items()}

        # Serialize complex objects to JSON strings
        return {
            "current_step": state_dict["current_step"],
            "challenge_data": json.dumps(state_dict.get("challenge_data"))
            if state_dict.get("challenge_data")
            else None,
            "seed_image_path": state_dict.get("seed_image_path"),
            "book_content": json.dumps(state_dict.get("book_content")) if state_dict.get("book_content") else None,
            "illustrations": json.dumps(state_dict.get("illustrations", {})),
            "pdf_path": state_dict.get("pdf_path"),
            "approvals": json.dumps(state_dict.get("approvals", {})),
            "created_at": state_dict["created_at"],
            "updated_at": state_dict["updated_at"],
        }

    def _deserialize_state(self, row: tuple) -> WorkflowState:
        """Deserialize database row to WorkflowState object."""
        (
            current_step,
            challenge_data_json,
            seed_image_path,
            book_content_json,
            illustrations_json,
            pdf_path,
            approvals_json,
            created_at,
            updated_at,
        ) = row

        # Parse JSON fields
        challenge_data = json.loads(challenge_data_json) if challenge_data_json else None
        book_content = json.loads(book_content_json) if book_content_json else None
        illustrations = json.loads(illustrations_json) if illustrations_json else {}
        approvals = json.loads(approvals_json) if approvals_json else {}

        # Create WorkflowState
        return WorkflowState(
            current_step=current_step,
            challenge_data=challenge_data,
            seed_image_path=seed_image_path,
            book_content=book_content,
            illustrations=illustrations,
            pdf_path=pdf_path,
            approvals=approvals,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
        )

    def _get_workflow_state_unlocked(self, conn: sqlite3.Connection, session_id: str) -> WorkflowState:
        """Get workflow state without acquiring lock (internal use only).

        Args:
            conn: Active database connection
            session_id: The session identifier

        Returns:
            WorkflowState for the session
        """
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT current_step, challenge_data, seed_image_path, book_content,
                       illustrations, pdf_path, approvals, created_at, updated_at
                FROM workflow_state
                WHERE session_id = ?
            """,
                (session_id,),
            )
            row = cursor.fetchone()

            if row is None:
                # Return default state for new session
                logger.info("Creating default workflow state", session_id=session_id)
                return WorkflowState()

            logger.info("Retrieved workflow state", session_id=session_id, current_step=row[0])
            return self._deserialize_state(row)

        except Exception as e:
            logger.error("Failed to get workflow state", session_id=session_id, error=str(e))
            # Return default state on error
            return WorkflowState()

    def get_workflow_state(self, session_id: str) -> WorkflowState:
        """Get the workflow state for a session.

        If no state exists, returns a new default state.

        Args:
            session_id: The session identifier

        Returns:
            WorkflowState for the session
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                return self._get_workflow_state_unlocked(conn, session_id)
            finally:
                conn.close()

    def update_workflow_state(self, session_id: str, **updates) -> None:
        """Update the workflow state for a session.

        Args:
            session_id: The session identifier
            **updates: Fields to update (e.g., current_step="narration", challenge_data=data)
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                # Get current state (using unlocked version since we already have the lock)
                current_state = self._get_workflow_state_unlocked(conn, session_id)

                # Apply updates
                for key, value in updates.items():
                    if hasattr(current_state, key):
                        setattr(current_state, key, value)

                # Update timestamp
                current_state.updated_at = datetime.now()

                # Serialize state
                serialized = self._serialize_state(current_state)

                # Check if record exists
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM workflow_state WHERE session_id = ?", (session_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing record
                    cursor.execute(
                        """
                        UPDATE workflow_state
                        SET current_step = ?, challenge_data = ?, seed_image_path = ?,
                            book_content = ?, illustrations = ?, pdf_path = ?,
                            approvals = ?, updated_at = ?
                        WHERE session_id = ?
                    """,
                        (
                            serialized["current_step"],
                            serialized["challenge_data"],
                            serialized["seed_image_path"],
                            serialized["book_content"],
                            serialized["illustrations"],
                            serialized["pdf_path"],
                            serialized["approvals"],
                            serialized["updated_at"],
                            session_id,
                        ),
                    )
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO workflow_state
                        (session_id, current_step, challenge_data, seed_image_path,
                         book_content, illustrations, pdf_path, approvals, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            session_id,
                            serialized["current_step"],
                            serialized["challenge_data"],
                            serialized["seed_image_path"],
                            serialized["book_content"],
                            serialized["illustrations"],
                            serialized["pdf_path"],
                            serialized["approvals"],
                            serialized["created_at"],
                            serialized["updated_at"],
                        ),
                    )

                conn.commit()
                logger.info(
                    "Updated workflow state",
                    session_id=session_id,
                    current_step=current_state.current_step,
                    updates=list(updates.keys()),
                )

            except Exception as e:
                logger.error("Failed to update workflow state", session_id=session_id, error=str(e))
                raise
            finally:
                conn.close()

    def is_step_completed(self, session_id: str, step: WorkflowStep) -> bool:
        """Check if a specific workflow step has been completed.

        Args:
            session_id: The session identifier
            step: The workflow step to check

        Returns:
            True if the step is completed, False otherwise
        """
        state = self.get_workflow_state(session_id)
        return state.is_step_completed(step)

    def mark_step_approved(self, session_id: str, step: WorkflowStep) -> None:
        """Mark a workflow step as approved by the parent.

        Args:
            session_id: The session identifier
            step: The workflow step to approve
        """
        state = self.get_workflow_state(session_id)
        state.approvals[step] = True
        self.update_workflow_state(session_id, approvals=state.approvals)
        logger.info("Marked step as approved", session_id=session_id, step=step)

    def can_proceed_to_next_step(self, session_id: str) -> bool:
        """Check if the workflow can proceed to the next step.

        Requires both completion and approval of the current step.

        Args:
            session_id: The session identifier

        Returns:
            True if the workflow can proceed, False otherwise
        """
        state = self.get_workflow_state(session_id)
        can_proceed = state.can_proceed_to_next_step()
        logger.info(
            "Checking if can proceed to next step",
            session_id=session_id,
            current_step=state.current_step,
            can_proceed=can_proceed,
            is_completed=state.is_step_completed(state.current_step),
            is_approved=state.is_step_approved(state.current_step),
        )
        return can_proceed

    def advance_to_next_step(self, session_id: str) -> Optional[WorkflowStep]:
        """Advance the workflow to the next step if possible.

        Args:
            session_id: The session identifier

        Returns:
            The new current step, or None if cannot advance
        """
        if not self.can_proceed_to_next_step(session_id):
            logger.warning("Cannot advance to next step", session_id=session_id)
            return None

        state = self.get_workflow_state(session_id)
        next_step = state.get_next_step()

        if next_step:
            self.update_workflow_state(session_id, current_step=next_step)
            logger.info("Advanced to next step", session_id=session_id, next_step=next_step)

        return next_step


# Global singleton instance
workflow_state_manager = WorkflowStateManager()
