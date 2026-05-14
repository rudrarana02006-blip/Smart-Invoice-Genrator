"""
Database module — async MongoDB connection using motor.
Handles connection lifecycle and provides collection accessors.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Global database references
client = None
db = None

async def connect_to_mongo():
    """Create MongoDB connection and verify."""
    global client, db
    try:
        # Create async client
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        
        # Access database
        db = client[settings.DB_NAME]
        
        # Send a ping to confirm a successful connection
        await client.admin.command('ping')
        print(f"✅ Successfully connected to MongoDB Atlas (Database: {settings.DB_NAME})")
        
        # Initialize collections & indexes
        await setup_indexes(db)
        
    except Exception as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close MongoDB connection gracefully."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")

async def setup_indexes(db):
    """Create necessary indexes for performance."""
    try:
        # Invoices: unique invoice_number per organization
        await db.invoices.drop_index("invoice_number_1") # Try to drop old unique index
        await db.invoices.create_index([("org_id", 1), ("invoice_number", 1)], unique=True)
        await db.invoices.create_index("status")
        
        # Clients: fast lookup by email
        await db.clients.create_index("email", unique=True)
        
        # Profiles: fast lookup by user_id
        await db.profiles.create_index("user_id", unique=True)
        
        # Users: fast lookup by email
        await db.users.create_index("email", unique=True)
        
        # OTPs: auto-expire after 5 minutes (300 seconds)
        await db.otps.create_index("created_at", expireAfterSeconds=300)
        
        print("✅ Database indexes verified.")
    except Exception as e:
        print(f"⚠️ Index setup warning: {e}")

# Helper functions to get specific collections
def get_invoice_collection():
    return db.invoices

# Added helper to provide raw db access for legacy imports
def get_db():
    """Return the main database object.
    This function maintains backward compatibility for modules that import
    ``get_db`` expecting a dictionary-like object with collection keys.
    """
    return db

def get_client_collection():
    return db.clients

def get_profile_collection():
    return db.profiles

def get_user_collection():
    return db.users

def get_otp_collection():
    return db.otps
