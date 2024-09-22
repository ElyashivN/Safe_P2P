from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class Encryption:
    def __init__(self):
        pass

    @staticmethod
    def generatePublicPrivateKeys():
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # # Serialize the private key
        # pem_private_key = private_key.private_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PrivateFormat.PKCS8,
        # )

        # Generate public key from the private key
        public_key = private_key.public_key()

        # # Serialize the public key
        # pem_public_key = public_key.public_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PublicFormat.SubjectPublicKeyInfo,
        # )

        return public_key, private_key

    @staticmethod
    def store(password, private_key,path=""):
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode())
        # encrypt the file in the computer
        # Serialize the private key
        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm,
        )

        with open(path+'private_key.pem', 'wb') as f:
            f.write(pem_private_key)
    @staticmethod
    def load(password, path=""):
        # Load the private key
        with open(path+'private_key.pem', 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=password,  # Use the same password used during encryption
            )
        return private_key
