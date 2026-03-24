import qrcode
import os

# your bank / payment info
account = "5133079382"   # your phone or account
name = "ZULBAYAR"

plans = {
    "7days": 3000,
    "1month": 10000,
    "6months": 30000,
    "1year": 50000
}

os.makedirs("qr_codes", exist_ok=True)

for plan, price in plans.items():
    data = f"ACC:{account}|AMT:{price}|DESC:{plan}"

    qr = qrcode.make(data)

    file_path = f"qr_codes/{plan}.png"
    qr.save(file_path)

    print(f"Generated: {file_path}")