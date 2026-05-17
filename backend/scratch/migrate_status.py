import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

async def migrate():
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DB_NAME", "smart_invoice")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    invoices = db["invoices"]
    
    print("Starting migration of status flags...")
    
    # 1. Paid
    res_paid = await invoices.update_many(
        {"status": "paid"},
        {"$set": {"is_sent": True, "is_paid": True}}
    )
    print(f"Updated {res_paid.modified_count} PAID invoices.")
    
    # 2. Sent / Overdue
    res_sent = await invoices.update_many(
        {"status": {"$in": ["sent", "overdue"]}},
        {"$set": {"is_sent": True, "is_paid": False}}
    )
    print(f"Updated {res_sent.modified_count} SENT/OVERDUE invoices.")
    
    # 3. Draft
    res_draft = await invoices.update_many(
        {"status": "draft"},
        {"$set": {"is_sent": False, "is_paid": False}}
    )
    print(f"Updated {res_draft.modified_count} DRAFT invoices.")
    
    # 4. Templates
    res_templates = await invoices.update_many(
        {"is_template": True},
        {"$set": {"is_sent": False, "is_paid": False}}
    )
    print(f"Ensured {res_templates.modified_count} templates are reset.")

    print("Migration complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
