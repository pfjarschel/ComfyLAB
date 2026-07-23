import pytest
import numpy as np
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.base import ExecutionContext
from comfylab.blocks.loader import load_all_blocks


@pytest.fixture(autouse=True)
def init_blocks():
    load_all_blocks()


@pytest.mark.asyncio
async def test_get_ndarray_item_1d():
    blueprint = {
        "blocks": [
            {"id": "get_item", "type": "Numeric Arrays/operations/get", "properties": {"Index": 1}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    block = engine.blocks["get_item"]
    block.properties["Array"] = np.array([10.0, 20.0, 30.0])

    item = await block.pull_data(context, "Item")
    assert item == 20.0
    assert isinstance(item, float)


@pytest.mark.asyncio
async def test_get_ndarray_item_2d_mxn():
    blueprint = {
        "blocks": [
            {"id": "get_item", "type": "Numeric Arrays/operations/get", "properties": {"Index": 0}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    block = engine.blocks["get_item"]
    arr_2d = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    block.properties["Array"] = arr_2d

    # Row 0
    item = await block.pull_data(context, "Item")
    assert item is not None
    assert isinstance(item, np.ndarray)
    np.testing.assert_array_equal(item, np.array([1.0, 2.0, 3.0]))

    # Row 1
    block.properties["Index"] = 1
    item1 = await block.pull_data(context, "Item")
    assert item1 is not None
    assert isinstance(item1, np.ndarray)
    np.testing.assert_array_equal(item1, np.array([4.0, 5.0, 6.0]))

    # Negative index -1 -> Row 1
    block.properties["Index"] = -1
    item_neg = await block.pull_data(context, "Item")
    np.testing.assert_array_equal(item_neg, np.array([4.0, 5.0, 6.0]))

    # Multi-dimensional string index "0, 1"
    block.properties["Index"] = "0, 1"
    item_multi = await block.pull_data(context, "Item")
    assert item_multi == 2.0

    # Multi-dimensional tuple index (1, 2)
    block.properties["Index"] = (1, 2)
    item_multi_tuple = await block.pull_data(context, "Item")
    assert item_multi_tuple == 6.0


@pytest.mark.asyncio
async def test_get_ndarray_item_chained():
    # Pass 2D array to block1 (Index=0), output to block2 (Index=1) -> should yield element (0,1)
    blueprint = {
        "blocks": [
            {"id": "b1", "type": "Numeric Arrays/operations/get", "properties": {"Index": 0}},
            {"id": "b2", "type": "Numeric Arrays/operations/get", "properties": {"Index": 1}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "b1", "source_pin": "Item", "target_block": "b2", "target_pin": "Array"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    b1 = engine.blocks["b1"]
    b2 = engine.blocks["b2"]
    b1.properties["Array"] = np.array([[10, 20, 30], [40, 50, 60]])

    val = await b2.pull_data(context, "Item")
    assert val == 20
    assert isinstance(val, (int, float))


@pytest.mark.asyncio
async def test_get_list_item_2d_and_mxn():
    blueprint = {
        "blocks": [
            {"id": "get_item", "type": "Lists/operations/get", "properties": {"Index": 0}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    block = engine.blocks["get_item"]

    # 1) Python nested list
    lst_2d = [[1, 2, 3], [4, 5, 6]]
    block.properties["List"] = lst_2d

    item0 = await block.pull_data(context, "Item")
    assert item0 == [1, 2, 3]

    block.properties["Index"] = 1
    item1 = await block.pull_data(context, "Item")
    assert item1 == [4, 5, 6]

    # Multi-index "1, 2"
    block.properties["Index"] = "1, 2"
    item_multi = await block.pull_data(context, "Item")
    assert item_multi == 6

    # 2) NumPy 2D array passed to Get List Item
    arr_2d = np.array([[10, 20], [30, 40]])
    block.properties["List"] = arr_2d
    block.properties["Index"] = 0
    item_arr0 = await block.pull_data(context, "Item")
    assert item_arr0 == [10, 20]

    block.properties["Index"] = 1
    item_arr1 = await block.pull_data(context, "Item")
    assert item_arr1 == [30, 40]


@pytest.mark.asyncio
async def test_get_item_edge_cases():
    blueprint = {
        "blocks": [
            {"id": "nd_get", "type": "Numeric Arrays/operations/get", "properties": {}},
            {"id": "lst_get", "type": "Lists/operations/get", "properties": {}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    nd_block = engine.blocks["nd_get"]
    lst_block = engine.blocks["lst_get"]

    # Out of bounds
    nd_block.properties["Array"] = np.array([[1, 2], [3, 4]])
    nd_block.properties["Index"] = 10
    assert await nd_block.pull_data(context, "Item") is None

    lst_block.properties["List"] = [[1, 2], [3, 4]]
    lst_block.properties["Index"] = 10
    assert await lst_block.pull_data(context, "Item") is None

    # None input
    nd_block.properties["Array"] = None
    assert await nd_block.pull_data(context, "Item") is None

    lst_block.properties["List"] = None
    assert await lst_block.pull_data(context, "Item") is None

    # Empty list / empty ndarray
    nd_block.properties["Array"] = np.array([])
    nd_block.properties["Index"] = 0
    assert await nd_block.pull_data(context, "Item") is None

    lst_block.properties["List"] = []
    lst_block.properties["Index"] = 0
    assert await lst_block.pull_data(context, "Item") is None
