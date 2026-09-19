import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.models.db import get_db

TEST_DB_URL = "sqlite:///./storage/test_contractlens.db"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    from pathlib import Path
    Path("./storage").mkdir(parents=True, exist_ok=True)
    db_file = "./storage/test_contractlens.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass

    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    import app.api.v1.contracts as contracts_mod
    contracts_mod.SessionLocal = TestingSessionLocal

    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    db_file = "./storage/test_contractlens.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_pdf_bytes():
    import fitz
    doc = fitz.open()
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text((50, 100), "SECTION 1. DEFINITIONS AND AGREEMENT TERMS", fontsize=14)
    p1.insert_text((50, 130), "This Master Agreement defines all relevant terms and conditions.", fontsize=10)
    p1.insert_text((50, 160), "SECTION 2. LIMITATION OF LIABILITY", fontsize=14)
    p1.insert_text((50, 190), "In no event shall liability exceed $100,000.", fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
