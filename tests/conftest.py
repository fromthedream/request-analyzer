import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_ISSUER"] = "AuthApi"
os.environ["JWT_AUDIENCE"] = "AuthApiClient"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"