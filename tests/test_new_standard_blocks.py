import pytest
import math
from comfylab.engine.executor import ExecutionEngine
from comfylab.blocks.base import ExecutionContext


@pytest.mark.asyncio
async def test_fft_block():
    blueprint = {
        "blocks": [
            {"id": "fft", "type": "math/signal_processing/fft", "properties": {}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    fft_block = engine.blocks["fft"]

    # 1) 64-sample sine at 2 Hz, X provided (10s total, dx=10/64 -> Nyquist 3.2 Hz)
    N = 64
    dx = 10.0 / N
    freq_true = 2.0
    import numpy as np
    t = np.array([i * dx for i in range(N)])
    signal = np.array([math.sin(2 * math.pi * freq_true * x) for x in t])

    fft_block.properties["Signal"] = signal
    fft_block.properties["X"] = t
    await fft_block.execute(context, "Analyze")

    spectrum = await fft_block.pull_data(context, "Spectrum")
    freqs = await fft_block.pull_data(context, "Frequencies")

    assert spectrum is not None
    assert isinstance(spectrum, np.ndarray)
    assert len(spectrum) == N // 2 + 1
    assert freqs is not None
    assert isinstance(freqs, np.ndarray)
    assert len(freqs) == len(spectrum)
    # Spectral resolution bin = 1 / (N*dx) = 1 / 10 = 0.1 Hz
    assert abs(freqs[1] - freqs[0] - 0.1) < 1e-6
    # Peak bin should be near freq_true / resolution = 2.0 / 0.1 = 20
    peak_bin = max(range(len(spectrum)), key=lambda i: spectrum[i])
    assert abs(freqs[peak_bin] - freq_true) < 0.2

    # 2) Without X -> Frequencies is empty array
    del fft_block.properties["X"]
    await fft_block.execute(context, "Analyze")
    spectrum2 = await fft_block.pull_data(context, "Spectrum")
    freqs2 = await fft_block.pull_data(context, "Frequencies")
    assert spectrum2 is not None
    assert isinstance(freqs2, np.ndarray) and len(freqs2) == 0

    # 3) Empty signal -> empty spectrum, empty frequencies
    fft_block.properties["Signal"] = np.array([])
    await fft_block.execute(context, "Analyze")
    spectrum3 = await fft_block.pull_data(context, "Spectrum")
    freqs3 = await fft_block.pull_data(context, "Frequencies")
    assert len(spectrum3) == 0
    assert len(freqs3) == 0


@pytest.mark.asyncio
async def test_subtraction_block():
    blueprint = {
        "blocks": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 15.5}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 5.2}},
            {"id": "sub", "type": "math/basic/subtract", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "num1", "source_pin": "Value", "target_block": "sub", "target_pin": "A"},
            {"id": "l2", "type": "data", "source_block": "num2", "source_pin": "Value", "target_block": "sub", "target_pin": "B"},
            {"id": "l3", "type": "data", "source_block": "sub", "source_pin": "Result", "target_block": "print", "target_pin": "Value"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    await engine.run(start_block_id="print", start_pin_name="In")
    assert abs(engine.blocks["print"].last_printed - 10.3) < 0.0001


@pytest.mark.asyncio
async def test_multiply_divide_power_trig_blocks():
    blueprint = {
        "blocks": [
            {"id": "mult", "type": "math/basic/multiply", "properties": {"A": 3.0, "B": 4.0}},
            {"id": "div", "type": "math/basic/divide", "properties": {"A": 12.0, "B": 3.0}},
            {"id": "pow", "type": "math/basic/power", "properties": {"Base": 2.0, "Exponent": 4.0}},
            {"id": "trig_sin", "type": "math/basic/trig", "properties": {"Value": 90.0, "Function": "sin", "UseDegrees": True}},
            {"id": "trig_cos", "type": "math/basic/trig", "properties": {"Value": math.pi, "Function": "cos", "UseDegrees": False}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    mult_res = await engine.blocks["mult"].pull_data(context, "Result")
    assert mult_res == 12.0

    div_res = await engine.blocks["div"].pull_data(context, "Result")
    assert div_res == 4.0

    pow_res = await engine.blocks["pow"].pull_data(context, "Result")
    assert pow_res == 16.0

    sin_res = await engine.blocks["trig_sin"].pull_data(context, "Result")
    assert abs(sin_res - 1.0) < 0.0001

    cos_res = await engine.blocks["trig_cos"].pull_data(context, "Result")
    assert abs(cos_res - (-1.0)) < 0.0001


@pytest.mark.asyncio
async def test_random_block():
    blueprint = {
        "blocks": [
            {"id": "rand_float", "type": "math/random/random", "properties": {"Min": 1.5, "Max": 2.5, "IntegerMode": False}},
            {"id": "rand_int", "type": "math/random/random", "properties": {"Min": 10.0, "Max": 20.0, "IntegerMode": True}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    val_float = await engine.blocks["rand_float"].pull_data(context, "Value")
    assert 1.5 <= val_float <= 2.5
    
    val_int = await engine.blocks["rand_int"].pull_data(context, "Value")
    assert 10.0 <= val_int <= 20.0
    assert val_int == int(val_int)


@pytest.mark.asyncio
async def test_list_blocks():
    blueprint = {
        "blocks": [
            {"id": "arr_create", "type": "Lists/manipulation/create", "properties": {"itemCount": 1, "Row 0": "10, 20, 30, test", "ParseNumbers": True}},
            {"id": "arr_len", "type": "Lists/operations/length", "properties": {}},
            {"id": "arr_get", "type": "Lists/operations/get", "properties": {"Index": 2}},
            {"id": "arr_concat", "type": "Lists/manipulation/concat", "properties": {"ListB": [40, 50]}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "arr_create", "source_pin": "List", "target_block": "arr_len", "target_pin": "List"},
            {"id": "l2", "type": "data", "source_block": "arr_create", "source_pin": "List", "target_block": "arr_get", "target_pin": "List"},
            {"id": "l3", "type": "data", "source_block": "arr_create", "source_pin": "List", "target_block": "arr_concat", "target_pin": "ListA"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    arr = await engine.blocks["arr_create"].pull_data(context, "List")
    assert arr == [10, 20, 30, "test"]
    
    length = await engine.blocks["arr_len"].pull_data(context, "Length")
    assert length == 4

    item = await engine.blocks["arr_get"].pull_data(context, "Item")
    assert item == 30

    concat_res = await engine.blocks["arr_concat"].pull_data(context, "Result")
    assert concat_res == [10, 20, 30, "test", 40, 50]


@pytest.mark.asyncio
async def test_ndarray_blocks():
    import numpy as np
    blueprint = {
        "blocks": [
            {"id": "arr_create", "type": "Numeric Arrays/manipulation/create", "properties": {"itemCount": 1, "Row 0": "10, 20, 30"}},
            {"id": "arr_len", "type": "Numeric Arrays/operations/length", "properties": {}},
            {"id": "arr_get", "type": "Numeric Arrays/operations/get", "properties": {"Index": 2}},
            {"id": "arr_concat", "type": "Numeric Arrays/manipulation/concat", "properties": {"ArrayB": np.array([40, 50])}},
            {"id": "arr_add", "type": "Numeric Arrays/operations/add_subtract", "properties": {"Operand": 5.0, "Operation": "add"}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_block": "arr_create", "source_pin": "Array", "target_block": "arr_len", "target_pin": "Array"},
            {"id": "l2", "type": "data", "source_block": "arr_create", "source_pin": "Array", "target_block": "arr_get", "target_pin": "Array"},
            {"id": "l3", "type": "data", "source_block": "arr_create", "source_pin": "Array", "target_block": "arr_concat", "target_pin": "ArrayA"},
            {"id": "l4", "type": "data", "source_block": "arr_create", "source_pin": "Array", "target_block": "arr_add", "target_pin": "Array"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    arr = await engine.blocks["arr_create"].pull_data(context, "Array")
    assert isinstance(arr, np.ndarray)
    assert np.allclose(arr, [10.0, 20.0, 30.0])
    
    length = await engine.blocks["arr_len"].pull_data(context, "Length")
    assert length == 3

    item = await engine.blocks["arr_get"].pull_data(context, "Item")
    assert item == 30.0

    concat_res = await engine.blocks["arr_concat"].pull_data(context, "Result")
    assert isinstance(concat_res, np.ndarray)
    assert np.allclose(concat_res, [10.0, 20.0, 30.0, 40.0, 50.0])

    add_res = await engine.blocks["arr_add"].pull_data(context, "Result")
    assert isinstance(add_res, np.ndarray)
    assert np.allclose(add_res, [15.0, 25.0, 35.0])


@pytest.mark.asyncio
async def test_string_blocks():
    blueprint = {
        "blocks": [
            {"id": "str_concat", "type": "string/concat", "properties": {"String A": "Hello ", "String B": "World"}},
            {"id": "str_format", "type": "string/format", "properties": {"Template": "{0} equals {1}", "Arg0": "pi", "Arg1": 3.1415}},
            {"id": "str_case", "type": "string/case", "properties": {"Text": "CoMfYlAb", "Mode": "Lower"}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    concat = await engine.blocks["str_concat"].pull_data(context, "Result")
    assert concat == "Hello World"
    
    formatted = await engine.blocks["str_format"].pull_data(context, "Result")
    assert formatted == "pi equals 3.1415"

    cased = await engine.blocks["str_case"].pull_data(context, "Result")
    assert cased == "comfylab"
