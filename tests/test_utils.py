import json

import pytest

from thumbling.utils import decrypt_string, load_bot_file, get_service_config


@pytest.fixture
def bot_file_config(tmpdir):
    secret_key = "E8rW7D6zdutZVEWcZoyxneWLMjN1Gb3DydzulAlm0oQ="
    encrypted_data = {
        "name": "example",
        "description": "example bot",
        "services": [
            {
                "type": "endpoint",
                "appId": "example-bot-app-id",
                "id": "128",
                "appPassword": "+6RAW+6ChG4RHD8njZ+q8w==!5Y9PAusZTJE2dPslRjjDSQqYVaclEho0DkcjKJwQTCY=",
                "endpoint": "http://localhost:8000/api/messages",
                "name": "development",
            },
            {
                "type": "luis",
                "id": "luis-id",
                "name": "example-luis",
                "version": "0.1",
                "appId": "luis-app-id",
                "authoringKey": "K2Z75KaSuUUfcSAOTKxpAQ==!fn02s4rxzP0do00td4q2DwhL/BtyMtbbi6UhOZghpw0=",
                "subscriptionKey": "TgEHlAR1p2hc+DnNWe/W1Q==!cVJyli9tChHMelBwFCCuhRy1/JKRR/mrF7w6AUXoHwQ=",
                "region": "westeurope",
            },
            {
                "type": "dispatch",
                "appId": "dispatch-app-id",
                "id": "dispatch-app-id",
                "authoringKey": "+bMvD7MHb5HUUub5eVSySg==!v/212mImthq8WKbO6ie7kxXp8VNtN5v+1ahXP2cS3CE=",
                "name": "dispatch-example",
                "serviceIds": [],
                "subscriptionKey": "IbPm0CuyoFdSGJTvtocp2A==!iZLGWus+Cis1W0Bd6uHHvS2TPSGB/5JT5LBkXHMDniw=",
                "version": "0.1",
            },
            {
                "type": "qna",
                "kbId": "knowledge-base-id",
                "name": "qna-example",
                "subscriptionKey": "lVWQRCrC74iEV4YN9OMASg==!wecZQ1pLrWQkcskycrWetdy6zrAZTIGvJy8ZqwtzCHw=",
                "id": "78d561e0-d398-11e8-a480-2136c62f5d24",
                "endpointKey": "z81Yiqx/DnFtRJWylK97oA==!rU7eU1OxNUfIut3Myys/kw==",
                "hostname": "https://qna.host.name/qnamaker",
            },
        ],
        "custom_services": [
            {
                "endpoint": "http://localhost:9000",
                "id": "1",
                "name": "development",
                "type": "prometheus",
            }
        ],
        "padlock": "u5rwSEz1RmagA0bcsYJQew==!ttBgW4+20U4kwqJvkU9gxWmd9RTHt0CVng65A6FIq79ZS39Qgg8FPv6a2o6sok4R",
        "version": "2.0",
        "secretKey": "",
    }
    decrypted_data = {
        "name": "example",
        "description": "example bot",
        "services": [
            {
                "appId": "example-bot-app-id",
                "appPassword": "secret-app-password",
                "endpoint": "http://localhost:8000/api/messages",
                "id": "128",
                "name": "development",
                "type": "endpoint",
            },
            {
                "appId": "luis-app-id",
                "authoringKey": "luis-secret-auth-key",
                "id": "luis-id",
                "name": "example-luis",
                "subscriptionKey": "luis-secret-sub-key",
                "type": "luis",
                "version": "0.1",
                "region": "westeurope",
            },
            {
                "appId": "dispatch-app-id",
                "authoringKey": "dispatch-auth-key",
                "id": "dispatch-app-id",
                "name": "dispatch-example",
                "serviceIds": [],
                "subscriptionKey": "dispatch-subscription-key",
                "type": "dispatch",
                "version": "0.1",
            },
            {
                "endpointKey": "endpoint-key",
                "hostname": "https://qna.host.name/qnamaker",
                "id": "78d561e0-d398-11e8-a480-2136c62f5d24",
                "kbId": "knowledge-base-id",
                "name": "qna-example",
                "subscriptionKey": "qna-subscription-key",
                "type": "qna",
            },
        ],
        "custom_services": [
            {
                "endpoint": "http://localhost:9000",
                "id": "1",
                "name": "development",
                "type": "prometheus",
            }
        ],
        "padlock": "u5rwSEz1RmagA0bcsYJQew==!ttBgW4+20U4kwqJvkU9gxWmd9RTHt0CVng65A6FIq79ZS39Qgg8FPv6a2o6sok4R",
        "version": "2.0",
        "secretKey": "",
    }
    bot_file = tmpdir.join("test.bot")
    bot_file.write(json.dumps(encrypted_data))
    return bot_file.strpath, decrypted_data, secret_key


def test_decrypt_string():
    encrypted_string = (
        "+6RAW+6ChG4RHD8njZ+q8w==!5Y9PAusZTJE2dPslRjjDSQqYVaclEho0DkcjKJwQTCY="
    )
    key = "E8rW7D6zdutZVEWcZoyxneWLMjN1Gb3DydzulAlm0oQ="

    result = decrypt_string(encrypted_string, key)
    assert result == "secret-app-password"


def test_load_bot_file(bot_file_config):
    bot_file_path, bot_expected, secret_key = bot_file_config
    assert load_bot_file(bot_file_path, secret_key) == bot_expected


@pytest.mark.parametrize(
    ("input", "id_in_list_of_expected"),
    [
        (("endpoint", "development"), 0),
        (("luis", "example-luis"), 1),
        (("dispatch", "dispatch-example"), 2),
        (("qna", "qna-example"), 3),
    ],
)
def test_get_service_config(bot_file_config, input, id_in_list_of_expected):
    _, decrypted_config, _ = bot_file_config
    result = get_service_config(decrypted_config["services"], *input)
    assert result == decrypted_config["services"][id_in_list_of_expected]
