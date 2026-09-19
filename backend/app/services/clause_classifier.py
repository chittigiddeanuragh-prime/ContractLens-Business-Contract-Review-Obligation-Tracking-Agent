import re
from typing import Any, Dict, List, Tuple
from app.core.config import settings

CLASSIFICATION_PATTERNS = {
    "definitions": [r"\bdefinitions?\b", r"\bdefined terms?\b"],
    "term": [r"\bterm\b", r"\bduration\b", r"\beffective date\b"],
    "renewal": [r"\brenew(al)?\b", r"\bauto(matic)? renew\b"],
    "termination": [r"\bterminat(ion|e)\b", r"\bcancell?ation\b"],
    "payment": [r"\bpayment\b", r"\binvoic(e|ing)\b", r"\bprice\b"],
    "fees": [r"\bfees?\b", r"\brates?\b", r"\bcharges?\b"],
    "liability": [r"\bliabilit(y|ies)\b", r"\blimitation of liability\b", r"\bdamages\b"],
    "indemnification": [r"\bindemnif(y|ication|ied)\b", r"\bhold harmless\b"],
    "confidentiality": [r"\bconfidential(ity)?\b", r"\bnon-disclosure\b", r"\bproprietary\b"],
    "ip": [r"\bintellectual property\b", r"\bip rights?\b", r"\bpatents?\b", r"\bcopyrights?\b"],
    "warranties": [r"\bwarrant(y|ies)\b", r"\bguarantees?\b"],
    "sla": [r"\bservice level\b", r"\bsla\b", r"\buptime\b"],
    "governing_law": [r"\bgoverning law\b", r"\bjurisdiction\b", r"\bapplicable law\b"],
    "dispute_resolution": [r"\bdispute\b", r"\barbitration\b", r"\bmediation\b"],
    "notices": [r"\bnotices?\b", r"\bcommunications?\b"],
    "assignment": [r"\bassignment\b", r"\btransfers?\b"],
    "force_majeure": [r"\bforce majeure\b", r"\bacts? of god\b"],
    "data_protection": [r"\bdata (protection|privacy|security)\b", r"\bgdpr\b"],
}


class ClauseClassifier:
    @staticmethod
    def classify_clause(heading: str, text: str) -> Tuple[str, float]:
        """Classifies a single clause based on heading and text content."""
        search_target = f"{heading or ''} {text[:300]}".lower()

        # Check heading first for high confidence
        if heading:
            h_lower = heading.lower()
            for clause_type, patterns in CLASSIFICATION_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, h_lower):
                        return clause_type, 0.95

        # Check text body
        for clause_type, patterns in CLASSIFICATION_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, search_target):
                    return clause_type, 0.85

        return "other", 0.70

    @classmethod
    def classify_clauses_batch(cls, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classifies a batch of clauses."""
        for c in clauses:
            clause_type, conf = cls.classify_clause(c.get("heading") or "", c.get("text") or "")
            c["clause_type"] = clause_type
            if "confidence" in c:
                c["confidence"] = min(c["confidence"], conf)
            else:
                c["confidence"] = conf
        return clauses
