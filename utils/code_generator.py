import secrets

async def generate_random_code():
    return secrets.randbelow(90000) + 10000  # 10000–99999
