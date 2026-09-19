import io
import time
import fitz
import pytest
from app.models.audit_log import AuditLog
from app.models.contract import ContractVersion


def create_simple_pdf():
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text((50, 100), "TEST CONTRACT TITLE AND MASTER AGREEMENT", fontsize=16)
    page.insert_text((50, 150), "1. Agreement Term. This agreement shall remain effective for twelve months from the effective date unless terminated early.", fontsize=12)
    page.insert_text((50, 180), "2. Payment Terms. Fees shall be paid within thirty days of invoice date.", fontsize=12)
    b = doc.tobytes()
    doc.close()
    return b


def test_upload_valid_pdf_and_parse(client):
    pdf_bytes = create_simple_pdf()
    files = {"file": ("test_contract.pdf", pdf_bytes, "application/pdf")}
    data = {"name": "Test Agreement", "counterparty": "Acme Inc"}

    response = client.post("/api/v1/contracts", files=files, data=data)
    assert response.status_code == 202
    resp_data = response.json()
    assert resp_data["duplicate"] is False
    contract_id = resp_data["contract_id"]
    version_id = resp_data["version_id"]

    # Poll status until parsed
    for _ in range(10):
        v_resp = client.get(f"/api/v1/contracts/{contract_id}/versions/{version_id}")
        assert v_resp.status_code == 200
        v_data = v_resp.json()
        if v_data["status"] in ["parsed", "segmented", "extracting", "ready", "ready_with_warnings"]:
            break
        time.sleep(0.2)

    assert v_data["status"] in ["parsed", "segmented", "extracting", "ready", "ready_with_warnings"]

    assert v_data["page_count"] == 1


def test_upload_duplicate_pdf_returns_200(client):
    pdf_bytes = create_simple_pdf()
    files = {"file": ("dup_contract.pdf", pdf_bytes, "application/pdf")}

    res1 = client.post("/api/v1/contracts", files=files)
    assert res1.status_code == 202
    res2 = client.post("/api/v1/contracts", files=files)
    assert res2.status_code == 200
    assert res2.json()["duplicate"] is True


def test_upload_invalid_non_pdf_fails(client):
    files = {"file": ("fake.pdf", b"NOT A PDF FILE DATA", "application/pdf")}
    res = client.post("/api/v1/contracts", files=files)
    assert res.status_code == 400
    assert "error" in res.json()
    assert res.json()["error"]["message"] == "Invalid file format: must be a PDF document."


def test_highlights_endpoint_valid_and_out_of_range(client):
    pdf_bytes = create_simple_pdf()
    files = {"file": ("highlight_test.pdf", pdf_bytes, "application/pdf")}

    res = client.post("/api/v1/contracts", files=files)
    contract_id = res.json()["contract_id"]
    version_id = res.json()["version_id"]

    # Wait for parsing
    time.sleep(0.5)

    # Highlights for valid range [0, 10]
    h_res = client.get(f"/api/v1/contracts/{contract_id}/versions/{version_id}/highlights?start=0&end=10")
    assert h_res.status_code == 200
    assert "highlights" in h_res.json()

    # Out of range highlights
    bad_res = client.get(f"/api/v1/contracts/{contract_id}/versions/{version_id}/highlights?start=9999&end=10000")
    assert bad_res.status_code == 400
    assert bad_res.json()["error"]["code"] == "BAD_REQUEST"
