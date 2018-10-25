import base64
import copy
import json
from uuid import UUID

from Crypto.Cipher import AES
import iso8601


ENCRYPTED_PROPERTIES = {
    "abs": ["endpointKey", "subscriptionKey"],
    "endpoint": ["appPassword"],
    "luis": ["authoringKey", "subscriptionKey"],
    "dispatch": ["authoringKey", "subscriptionKey"],
    "file": [],
    "qna": ["subscriptionKey", "endpointKey"],
}


class BotConfigError(Exception):
    """
    Decrypting of an encrypted value failed
    """


def _unpad(s):
    return s[: -ord(s[len(s) - 1 :])]


def decrypt_string(encrypted_string: str, key: str) -> str:
    """ decrypt AES encrypted strings and remove padding bytes
    """
    if not encrypted_string:
        return ""

    if not key:
        raise BotConfigError("not secret provided for decryption")

    iv_base64, content_base64 = encrypted_string.split("!")
    aes = AES.new(base64.b64decode(key), AES.MODE_CBC, base64.b64decode(iv_base64))
    return _unpad(aes.decrypt(base64.b64decode(content_base64)).decode("utf-8"))


def decrypt_config(input_config: dict, key: str) -> dict:
    """ decrypt the properties of bot service configs

    Decrypt the values of service config keys which hold secrets and could
    be encrypted and return a decrypted configuration.
    """
    updated_config = copy.deepcopy(input_config)
    updated_config["services"] = []
    for service in input_config.get("services", []):
        updated_service = copy.copy(service)
        for encrypted_property in ENCRYPTED_PROPERTIES[service["type"]]:
            updated_service[encrypted_property] = decrypt_string(
                updated_service[encrypted_property], key
            )
        updated_config["services"].append(updated_service)
    return updated_config


def load_bot_file(file_path: str, key: str) -> dict:
    """ load a .bot file and decrypt it if the padlock is not empty
    """
    with open(file_path) as fo:
        plain_config = json.load(fo)

    is_encrypted = "padlock" in plain_config
    if not is_encrypted:
        return plain_config

    # msbot tool writes a uuid4 during encryption so we check if it is a valid value
    if "padlock" not in plain_config and not UUID(
        decrypt_string(plain_config["padlock"], key), version=4
    ):
        raise BotConfigError("padlock can not be decrypted with secret")

    return decrypt_config(plain_config, key)


def get_service_config(service_section: list, service_type: str, name: str) -> dict:
    service = [
        service_entry
        for service_entry in service_section
        if service_entry["type"] == service_type and service_entry["name"] == name
    ]
    num_services = len(service)
    if num_services != 1:
        raise BotConfigError(
            f"could not find exact one service config entry, instead {num_services}"
        )

    return service[0]


def str2timestamp(t: str) -> int:
    try:
        return int(t)
    except ValueError:
        return int(iso8601.parse_date(t).timestamp())
