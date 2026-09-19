import uuid
import pytest
from app.models.contract import Contract, ContractVersion
from app.services.pdf_parser import PDFParser
from app.services.clause_segmenter import ClauseSegmenter
from app.services.clause_classifier import ClauseClassifier
from app.models.clause import Clause
from app.agents.field_extractor import FieldExtractorAgent
from app.services.risk_analyzer import RiskAnalyzerService


def test_risk_analyzer_service(db_session, sample_pdf_bytes):
    parse_res = PDFParser.parse_pdf_bytes(sample_pdf_bytes)
    raw_clauses = ClauseSegmenter.segment_contract(parse_res["canonical_text"], parse_res["pages_data"])
    classified_clauses = ClauseClassifier.classify_clauses_batch(raw_clauses)

    c_id = str(uuid.uuid4())
    v_id = str(uuid.uuid4())

    contract = Contract(
        id=c_id,
        title="Risk Test Contract",
        filename="test.pdf",
        file_hash="hash_" + c_id[:8],
        file_path="/tmp/test.pdf",
        file_size=len(sample_pdf_bytes),
        mime_type="application/pdf",
        status="ready"
    )
    db_session.add(contract)

    version = ContractVersion(
        id=v_id,
        contract_id=c_id,
        version_number=1,
        file_hash=contract.file_hash,
        file_path=contract.file_path,
        canonical_text=parse_res["canonical_text"],
        page_count=parse_res["page_count"],
        status="ready"
    )
    db_session.add(version)
    db_session.commit()

    # Save clauses
    for idx, c_data in enumerate(classified_clauses):
        c_rec = Clause(
            id=str(uuid.uuid4()),
            contract_id=c_id,
            version_id=v_id,
            number=c_data["number"],
            heading=c_data["heading"],
            text=c_data["text"],
            page_start=c_data["page_start"],
            page_end=c_data["page_end"],
            order_index=idx,
            level=1,
            clause_type=c_data["clause_type"],
            char_start=c_data["char_start"],
            char_end=c_data["char_end"]
        )
        db_session.add(c_rec)
    db_session.commit()

    # Extract fields
    FieldExtractorAgent(db_session).extract_fields_for_version(v_id)

    # Analyze risks
    res = RiskAnalyzerService.analyze_risks_for_version(db_session, v_id)

    assert "overall_risk_score" in res
    assert 0.0 <= res["overall_risk_score"] <= 100.0
    assert "risk_items" in res
    assert isinstance(res["risk_items"], list)
    assert len(res["risk_items"]) > 0

    # Verify every risk item has valid severity and quote grounded in canonical text
    for r in res["risk_items"]:
        assert r["severity"] in ("critical", "high", "medium", "low")
        assert r["status"] in ("verified", "unverified")
        if r["quote"]:
            assert r["quote"] in parse_res["canonical_text"] or r["quote"].lower() in parse_res["canonical_text"].lower()


def test_risk_api_endpoints(client, db_session, sample_pdf_bytes):
    parse_res = PDFParser.parse_pdf_bytes(sample_pdf_bytes)

    c_id = str(uuid.uuid4())
    v_id = str(uuid.uuid4())

    contract = Contract(
        id=c_id,
        title="API Risk Test Contract",
        filename="test_api.pdf",
        file_hash="hash_api_" + c_id[:8],
        file_path="/tmp/test_api.pdf",
        file_size=len(sample_pdf_bytes),
        mime_type="application/pdf",
        status="ready"
    )
    db_session.add(contract)

    version = ContractVersion(
        id=v_id,
        contract_id=c_id,
        version_number=1,
        file_hash=contract.file_hash,
        file_path=contract.file_path,
        canonical_text=parse_res["canonical_text"],
        page_count=parse_res["page_count"],
        status="ready"
    )
    db_session.add(version)
    db_session.commit()

    # Test POST analyze endpoint
    resp_post = client.post(f"/api/v1/contracts/{c_id}/risk/analyze")
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["contract_id"] == c_id
    assert "overall_risk_score" in data_post
    assert "risk_items" in data_post

    # Test GET risks endpoint
    resp_get = client.get(f"/api/v1/contracts/{c_id}/risk")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["contract_id"] == c_id
    assert len(data_get["risk_items"]) == len(data_post["risk_items"])

    # Test GET with filter
    resp_filt = client.get(f"/api/v1/contracts/{c_id}/risk?is_anomaly=true")
    assert resp_filt.status_code == 200
    data_filt = resp_filt.json()
    for item in data_filt["risk_items"]:
        assert item["is_anomaly"] is True
