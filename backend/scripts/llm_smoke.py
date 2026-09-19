import asyncio
import sys
import time
from pathlib import Path
from pydantic import BaseModel

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.models.db import SessionLocal, init_db
from app.llm.client import LLMClient
from app.llm.safety import wrap_untrusted, SYSTEM_PREAMBLE


class PingResult(BaseModel):
    status: str
    contract_type: str
    summary: str


async def main():
    print("=====================================================")
    print("ContractLens LLM Smoke Test Script")
    print("=====================================================")
    print(f"Primary Provider:   {settings.LLM_PRIMARY}")
    print(f"Fallback Chain:     {settings.LLM_FALLBACKS}")
    print(f"Configured Keys:    {settings.get_configured_providers()}")
    print("=====================================================\n")

    init_db()
    db = SessionLocal()

    sample_contract_text = (
        "This Master Services Agreement is entered into between Acme Corp ('Client') "
        "and Beta LLC ('Provider') effective as of January 1, 2026."
    )
    user_prompt = wrap_untrusted(sample_contract_text)
    test_hash = "smoke_hash_sample_001"

    print("Executing LLM Run #1 (Expecting Network Call or Fallback)...")
    start_time = time.time()
    try:
        res1 = await LLMClient.run(
            task="ping_extract",
            schema=PingResult,
            system=SYSTEM_PREAMBLE,
            user=user_prompt,
            file_hash=test_hash,
            db=db,
        )
        elapsed1 = int((time.time() - start_time) * 1000)
        print(f"SUCCESS Run #1 in {elapsed1} ms:")
        print(f"   Output: {res1}\n")
    except Exception as e:
        print(f"Run #1 Exception: {e}\n")

    print("Executing LLM Run #2 with same file_hash (Expecting DB Cache Hit)...")
    start_time = time.time()
    try:
        res2 = await LLMClient.run(
            task="ping_extract",
            schema=PingResult,
            system=SYSTEM_PREAMBLE,
            user=user_prompt,
            file_hash=test_hash,
            db=db,
        )
        elapsed2 = int((time.time() - start_time) * 1000)
        print(f"SUCCESS Run #2 in {elapsed2} ms (Cache Hit Demo):")
        print(f"   Output: {res2}\n")
    except Exception as e:
        print(f"Run #2 Exception: {e}\n")

    db.close()
    print("Smoke test finished.")


if __name__ == "__main__":
    asyncio.run(main())
