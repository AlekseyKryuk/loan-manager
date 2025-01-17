from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class HashPassword:
    @staticmethod
    def create_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_hash(plain_password: str, hashes_password: str) -> bool:
        return pwd_context.verify(plain_password, hashes_password)


hash_password = HashPassword()
