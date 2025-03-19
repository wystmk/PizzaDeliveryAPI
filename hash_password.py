from passlib.context import CryptContext

# Setup bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash the password "password"
hashed_password = pwd_context.hash("password")

# Print the hashed password
print("Hashed Password:", hashed_password)