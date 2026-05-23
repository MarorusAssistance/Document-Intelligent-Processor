from __future__ import annotations

import pytest

from document_processor.domain.documents.models import DocumentStatus
from document_processor.domain.documents.state_machine import (
    VALID_TRANSITIONS,
    InvalidTransition,
    assert_valid_transition,
)


class TestValidTransitions:
    def test_uploaded_to_processing(self) -> None:
        assert_valid_transition(DocumentStatus.uploaded, DocumentStatus.processing)

    def test_uploaded_to_failed(self) -> None:
        assert_valid_transition(DocumentStatus.uploaded, DocumentStatus.failed)

    def test_processing_to_extracted(self) -> None:
        assert_valid_transition(DocumentStatus.processing, DocumentStatus.extracted)

    def test_extracted_to_pending_review(self) -> None:
        assert_valid_transition(DocumentStatus.extracted, DocumentStatus.pending_review)

    def test_pending_review_to_approved(self) -> None:
        assert_valid_transition(DocumentStatus.pending_review, DocumentStatus.approved)

    def test_pending_review_to_rejected(self) -> None:
        assert_valid_transition(DocumentStatus.pending_review, DocumentStatus.rejected)

    def test_approved_to_pushing(self) -> None:
        assert_valid_transition(DocumentStatus.approved, DocumentStatus.pushing)

    def test_pushing_to_pushed(self) -> None:
        assert_valid_transition(DocumentStatus.pushing, DocumentStatus.pushed)

    def test_rejected_can_return_to_pending_review(self) -> None:
        assert_valid_transition(DocumentStatus.rejected, DocumentStatus.pending_review)


class TestInvalidTransitions:
    def test_uploaded_cannot_go_to_approved(self) -> None:
        with pytest.raises(InvalidTransition) as exc_info:
            assert_valid_transition(DocumentStatus.uploaded, DocumentStatus.approved)
        assert exc_info.value.from_status == DocumentStatus.uploaded
        assert exc_info.value.to_status == DocumentStatus.approved

    def test_pushed_is_terminal(self) -> None:
        for target in DocumentStatus:
            with pytest.raises(InvalidTransition):
                assert_valid_transition(DocumentStatus.pushed, target)

    def test_failed_is_terminal(self) -> None:
        for target in DocumentStatus:
            with pytest.raises(InvalidTransition):
                assert_valid_transition(DocumentStatus.failed, target)

    def test_processing_cannot_skip_to_pending_review(self) -> None:
        with pytest.raises(InvalidTransition):
            assert_valid_transition(DocumentStatus.processing, DocumentStatus.pending_review)

    def test_approved_cannot_go_back_to_uploaded(self) -> None:
        with pytest.raises(InvalidTransition):
            assert_valid_transition(DocumentStatus.approved, DocumentStatus.uploaded)


class TestTransitionTable:
    def test_all_statuses_have_entries(self) -> None:
        for status in DocumentStatus:
            assert status in VALID_TRANSITIONS, f"{status} missing from VALID_TRANSITIONS"

    def test_invalid_transition_message_contains_statuses(self) -> None:
        exc = InvalidTransition(DocumentStatus.uploaded, DocumentStatus.pushed)
        assert "uploaded" in str(exc)
        assert "pushed" in str(exc)
