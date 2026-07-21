import pytest
from pydantic import ValidationError
from comfylab.engine.models import BlueprintModel

def test_valid_blueprint_parsing():
    blueprint_json = {
        "blocks": [
            {
                "id": "block_1",
                "type": "constants/number",
                "properties": {"value": 42.0}
            },
            {
                "id": "block_2",
                "type": "outputs/basic/print",
                "properties": {}
            }
        ],
        "links": [
            {
                "id": "link_1",
                "type": "data",
                "source_block": "block_1",
                "source_pin": "Value",
                "target_block": "block_2",
                "target_pin": "Value"
            }
        ]
    }

    blueprint = BlueprintModel.model_validate(blueprint_json)
    assert len(blueprint.blocks) == 2
    assert len(blueprint.links) == 1
    assert blueprint.blocks[0].id == "block_1"
    assert blueprint.links[0].type == "data"


def test_invalid_blueprint_missing_fields():
    # Missing 'type' in link
    invalid_json = {
        "blocks": [
            {
                "id": "block_1",
                "type": "constants/number"
            }
        ],
        "links": [
            {
                "id": "link_1",
                "source_block": "block_1",
                "source_pin": "Value",
                "target_block": "block_2",
                "target_pin": "Value"
            }
        ]
    }

    with pytest.raises(ValidationError):
        BlueprintModel.model_validate(invalid_json)


def test_invalid_link_type():
    # 'type' is not Literal['exec', 'data']
    invalid_json = {
        "blocks": [],
        "links": [
            {
                "id": "link_1",
                "type": "invalid_type",
                "source_block": "block_1",
                "source_pin": "Value",
                "target_block": "block_2",
                "target_pin": "Value"
            }
        ]
    }

    with pytest.raises(ValidationError):
        BlueprintModel.model_validate(invalid_json)
