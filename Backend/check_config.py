import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required configuration keys
required_keys = [
    'VERTEIL_API_BASE_URL',
    'VERTEIL_TOKEN_ENDPOINT',
    'VERTEIL_USERNAME',
    'VERTEIL_PASSWORD',
    'VERTEIL_THIRD_PARTY_ID',
    'VERTEIL_OFFICE_ID'
]

print("Checking environment configuration...\n")

# Check each required key
missing_keys = []
for key in required_keys:
    value = os.environ.get(key)
    if not value:
        missing_keys.append(key)
        print(f"❌ {key}: (missing)")
    else:
        # Mask sensitive values
        display_value = value if key not in ['VERTEIL_PASSWORD'] else '********'
        print(f"✅ {key}: {display_value}")

# Print results
if missing_keys:
    print("\n❌ Missing required environment variables:")
    for key in missing_keys:
        print(f"  - {key}")
    print("\nPlease set these variables in your .env file or environment.")
else:
    print("\n✅ All required environment variables are set!")
