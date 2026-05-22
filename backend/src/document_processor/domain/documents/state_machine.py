from __future__ import annotations

from document_processor.domain.documents.models import DocumentStatus

VALID_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.uploaded: frozenset({DocumentStatus.processing, DocumentStatus.failed}),
    DocumentStatus.processing: frozenset({DocumentStatus.extracted, DocumentStatus.failed}),
    DocumentStatus.extracted: frozenset({DocumentStatus.pending_review, DocumentStatus.failed}),
    DocumentStatus.pending_review: frozenset({
        DocumentStatus.approved,
        DocumentStatus.rejected,
        DocumentStatus.failed,
    }),
    DocumentStatus.approved: frozenset({DocumentStatus.pushing, DocumentStatus.failed}),
    DocumentStatus.pushing: frozenset({DocumentStatus.pushed, DocumentStatus.failed}),
    DocumentStatus.pushed: frozenset(),
    DocumentStatus.rejected: frozenset({DocumentStatus.pending_review, DocumentStatus.failed}),
    DocumentStatus.failed: frozenset(),
}


class InvalidTransition(Exception):
    def __init__(self, from_status: DocumentStatus, to_status: DocumentStatus) -> None:
        super().__init__(f"Invalid transition: {from_status} → {to_status}")
        self.from_status = from_status
        self.to_status = to_status


def assert_valid_transition(
    from_status: DocumentStatus,
    to_status: DocumentStatus,
) -> None:
    allowed = VALID_TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise InvalidTransition(from_status, to_status)
