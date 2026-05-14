"""
Numbering Service — Atomic Sequential Numbering.
Uses MongoDB findOneAndUpdate for thread-safe increments per Organization.
"""

from config import settings

def get_counters_collection():
    from database import db
    return db.counters

async def get_next_sequence_value(org_id: str, prefix: str = "INV-") -> int:
    """
    Atoms: Increments a counter for a specific org/prefix combination.
    """
    counters = get_counters_collection()
    
    from pymongo import ReturnDocument
    
    result = await counters.find_one_and_update(
        {"org_id": org_id, "prefix": prefix},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    
    return result["sequence_value"]

async def format_invoice_number(org_id: str, prefix: str, padding: int = 4) -> str:
    """
    Combines prefix + atomic sequence.
    Example: org123, "DEV-", 3 -> "DEV-001"
    """
    seq = await get_next_sequence_value(org_id, prefix)
    return f"{prefix}{str(seq).zfill(padding)}"
