import bcrypt

password = input("Enter password to hash: ").strip()

if not password:
    print("No password provided.")
else:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print("Hashed password generated:")
    print(hashed)
