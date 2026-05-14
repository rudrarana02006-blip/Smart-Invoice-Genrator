import asyncio
import os
import sys

# Add the current directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_mongo, get_otp_collection

async def main():
    await connect_to_mongo()
    otps = get_otp_collection()
    
    # Get the most recent OTP
    latest_otp = await otps.find_one(sort=[("created_at", -1)])
    
    if latest_otp:
        print(f"\n[DEBUG] Latest OTP for {latest_otp['email']}: {latest_otp['otp']}\n")
    else:
        print("\n[DEBUG] No OTP found in the database.\n")

if __name__ == "__main__":
    asyncio.run(main())
