# security/encryption.py

import os
from cryptography.fernet import Fernet


class DataEncryption:

    def __init__(self, key=None):

        if key is None:

            key = os.environ.get(
                "SECUREFLOW_ENCRYPTION_KEY"
            )

        if not key:

            raise ValueError(
                "Encryption key is missing"
            )

        self.cipher = Fernet(
            key.encode()
            if isinstance(key, str)
            else key
        )

    def encrypt(self, value):

        encrypted = self.cipher.encrypt(
            value.encode()
        )

        return encrypted.decode()

    def decrypt(self, encrypted_value):

        decrypted = self.cipher.decrypt(
            encrypted_value.encode()
        )

        return decrypted.decode()