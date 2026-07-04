from decimal import Decimal

from mfrecon.core.domain import CRMRecord
from mfrecon.validators.schema import SchemaValidator


def test_schema_validator_success():
    validator = SchemaValidator()

    record = CRMRecord(
        crm_client_id="CRM001",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )

    required = ["pan", "investor_name"]
    available = ["pan", "investor_name", "mobile", "email", "total_amount"]

    failures = validator.validate(record, required, available)
    assert len(failures) == 0


def test_schema_validator_missing_required():
    validator = SchemaValidator()

    # Empty investor_name (required)
    record = CRMRecord(
        crm_client_id="CRM001",
        pan="ABCDE1234F",
        investor_name="   ",  # whitespace
        mobile="9876543210",
        email="ramesh@gmail.com",
        total_amount=Decimal("100.00")
    )

    required = ["pan", "investor_name"]
    available = ["pan", "investor_name", "mobile", "email", "total_amount"]

    failures = validator.validate(record, required, available)
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "REQUIRED_FIELD_MISSING"
    assert failures[0]["field_name"] == "investor_name"


def test_schema_validator_unexpected_populated_field():
    validator = SchemaValidator()

    # mobile is populated, but NOT in available fields list
    record = CRMRecord(
        crm_client_id="CRM001",
        pan="ABCDE1234F",
        investor_name="Ramesh Sharma",
        mobile="9876543210",
        email=None,
        total_amount=Decimal("0.00")
    )

    required = ["pan", "investor_name"]
    available = ["pan", "investor_name", "total_amount"]  # mobile is omitted

    failures = validator.validate(record, required, available)
    assert len(failures) == 1
    assert failures[0]["failure_type"] == "UNEXPECTED_FIELD"
    assert failures[0]["field_name"] == "mobile"
