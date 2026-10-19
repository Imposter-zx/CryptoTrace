"""Unit tests for Investigation Pydantic schemas."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.investigations import InvestigationPriority, InvestigationStatus
from app.schemas.investigations import InvestigationCreate, InvestigationUpdate


class TestInvestigationCreate:
    def test_valid_minimal(self):
        data = InvestigationCreate(title="Test Investigation")
        assert data.title == "Test Investigation"
        assert data.status == InvestigationStatus.DRAFT
        assert data.priority == InvestigationPriority.MEDIUM

    def test_title_stripped(self):
        data = InvestigationCreate(title="  My Case  ")
        assert data.title == "My Case"

    def test_blank_title_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            InvestigationCreate(title="   ")
        assert "blank" in str(exc_info.value).lower()

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            InvestigationCreate(title="x" * 256)

    def test_tags_validated(self):
        data = InvestigationCreate(title="Case", tags=["crypto", "ransomware"])
        assert "crypto" in data.tags

    def test_too_many_tags_rejected(self):
        with pytest.raises(ValidationError):
            InvestigationCreate(title="Case", tags=[f"tag{i}" for i in range(51)])

    def test_all_statuses_accepted(self):
        for status in InvestigationStatus:
            data = InvestigationCreate(title="Case", status=status)
            assert data.status == status

    def test_all_priorities_accepted(self):
        for priority in InvestigationPriority:
            data = InvestigationCreate(title="Case", priority=priority)
            assert data.priority == priority

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            InvestigationCreate(title="Case", status="invalid_status")


class TestInvestigationUpdate:
    def test_partial_update_allowed(self):
        data = InvestigationUpdate(title="New Title")
        assert data.title == "New Title"
        assert data.status is None
        assert data.priority is None

    def test_empty_update_allowed(self):
        data = InvestigationUpdate()
        dump = data.model_dump(exclude_unset=True)
        assert dump == {}
