import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from cryptography.hazmat.primitives import padding

from app.config import GRUMMER_SECRET_KEY


def decrypt_grummer(payload: dict) -> str:
    """
    Recebe payload criptografado do gateway Grummer
    e devolve o JSON original descriptografado.
    """

    try:
        # Chave AES
        #
        # A secret chega em hexadecimal.
        #
        # Ex:
        # "bd8fe643a6e1..."
        #
        # Precisamos converter para bytes.
        key = bytes.fromhex(GRUMMER_SECRET_KEY)

        # IV recebido em Base64
        #
        # Ex:
        # "Sc8ZOj8NsOWy7lgAwWOioQ=="
        #
        # Decodifica para bytes.
        iv = base64.b64decode(payload["iv"])

        # Ciphertext recebido em Base64 é o JSON criptografado.
        ciphertext = base64.b64decode(payload["ciphertext"])

        # Cria objeto AES em modo CBC
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))

        # Inicializa descriptografia
        decryptor = cipher.decryptor()

        # Executa descriptografia
        #
        # Ainda contém padding PKCS7.
        padded_data = (decryptor.update(ciphertext) + decryptor.finalize())

        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()

        data = (unpadder.update(padded_data) + unpadder.finalize())

        # Converte bytes -> string
        #
        # Resultado:
        #
        # {
        #   "transaction_id": ...
        # }
        return data.decode("utf-8")

    except Exception as e:

        raise ValueError(f"decrypt_failed: {str(e)}")