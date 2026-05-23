from __future__ import annotations

from dataclasses import dataclass

from document_processor.application.documents.get_document import DocumentNotFound
from document_processor.application.ports.documents_repository import DocumentsRepository
from document_processor.domain.documents.models import Correction, ExtractedField
from document_processor.domain.documents.value_objects import Money


@dataclass(frozen=True)
class ApplyCorrectionCommand:
    client_id: str
    document_id: str
    field_id: str
    new_value: str | Money
    corrected_by: str
    reason: str | None = None


@dataclass(frozen=True)
class ApplyCorrectionResult:
    correction: Correction
    field: ExtractedField


async def apply_correction(
    command: ApplyCorrectionCommand,
    documents_repo: DocumentsRepository,
) -> ApplyCorrectionResult:
    # TODO(M2): transactional batch — Correction create + ExtractedField update atomically
    document = await documents_repo.get(command.client_id, command.document_id)
    if document is None:
        raise DocumentNotFound(command.client_id, command.document_id)

    raise NotImplementedError("apply_correction is implemented in M2")
