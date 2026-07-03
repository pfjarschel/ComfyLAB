import pytest
import math
from comfylab.engine.executor import ExecutionEngine
from comfylab.nodes.base import ExecutionContext


@pytest.mark.asyncio
async def test_fft_node():
    blueprint = {
        "nodes": [
            {"id": "fft", "type": "math/signal_processing/fft", "properties": {}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)

    fft_node = engine.nodes["fft"]

    # 1) 64-sample sine at 2 Hz, X provided (10s total, dx=10/64 -> Nyquist 3.2 Hz)
    N = 64
    dx = 10.0 / N
    freq_true = 2.0
    t = [i * dx for i in range(N)]
    signal = [math.sin(2 * math.pi * freq_true * x) for x in t]

    fft_node.properties["Signal"] = signal
    fft_node.properties["X"] = t
    await fft_node.execute(context, "Analyze")

    spectrum = await fft_node.pull_data(context, "Spectrum")
    freqs = await fft_node.pull_data(context, "Frequencies")

    assert spectrum is not None
    assert len(spectrum) == N // 2 + 1
    assert freqs is not None
    assert len(freqs) == len(spectrum)
    # Spectral resolution bin = 1 / (N*dx) = 1 / 10 = 0.1 Hz
    assert abs(freqs[1] - freqs[0] - 0.1) < 1e-6
    # Peak bin should be near freq_true / resolution = 2.0 / 0.1 = 20
    peak_bin = max(range(len(spectrum)), key=lambda i: spectrum[i])
    assert abs(freqs[peak_bin] - freq_true) < 0.2

    # 2) Without X -> Frequencies is None
    del fft_node.properties["X"]
    await fft_node.execute(context, "Analyze")
    spectrum2 = await fft_node.pull_data(context, "Spectrum")
    freqs2 = await fft_node.pull_data(context, "Frequencies")
    assert spectrum2 is not None
    assert freqs2 is None

    # 3) Empty signal -> empty spectrum, None frequencies
    fft_node.properties["Signal"] = []
    await fft_node.execute(context, "Analyze")
    spectrum3 = await fft_node.pull_data(context, "Spectrum")
    freqs3 = await fft_node.pull_data(context, "Frequencies")
    assert spectrum3 == []
    assert freqs3 is None


@pytest.mark.asyncio
async def test_subtraction_node():
    blueprint = {
        "nodes": [
            {"id": "num1", "type": "constants/number", "properties": {"value": 15.5}},
            {"id": "num2", "type": "constants/number", "properties": {"value": 5.2}},
            {"id": "sub", "type": "math/arithmetic/subtract", "properties": {}},
            {"id": "print", "type": "outputs/basic/print", "properties": {}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "num1", "source_pin": "Value", "target_node": "sub", "target_pin": "A"},
            {"id": "l2", "type": "data", "source_node": "num2", "source_pin": "Value", "target_node": "sub", "target_pin": "B"},
            {"id": "l3", "type": "data", "source_node": "sub", "source_pin": "Result", "target_node": "print", "target_pin": "Value"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    await engine.run(start_node_id="print", start_pin_name="In")
    assert abs(engine.nodes["print"].last_printed - 10.3) < 0.0001


@pytest.mark.asyncio
async def test_multiply_divide_power_trig_nodes():
    blueprint = {
        "nodes": [
            {"id": "mult", "type": "math/arithmetic/multiply", "properties": {"A": 3.0, "B": 4.0}},
            {"id": "div", "type": "math/arithmetic/divide", "properties": {"A": 12.0, "B": 3.0}},
            {"id": "pow", "type": "math/arithmetic/power", "properties": {"Base": 2.0, "Exponent": 4.0}},
            {"id": "trig_sin", "type": "math/trigonometry/trig", "properties": {"Value": 90.0, "Function": "sin", "UseDegrees": True}},
            {"id": "trig_cos", "type": "math/trigonometry/trig", "properties": {"Value": math.pi, "Function": "cos", "UseDegrees": False}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    mult_res = await engine.nodes["mult"].pull_data(context, "Result")
    assert mult_res == 12.0

    div_res = await engine.nodes["div"].pull_data(context, "Result")
    assert div_res == 4.0

    pow_res = await engine.nodes["pow"].pull_data(context, "Result")
    assert pow_res == 16.0

    sin_res = await engine.nodes["trig_sin"].pull_data(context, "Result")
    assert abs(sin_res - 1.0) < 0.0001

    cos_res = await engine.nodes["trig_cos"].pull_data(context, "Result")
    assert abs(cos_res - (-1.0)) < 0.0001


@pytest.mark.asyncio
async def test_random_node():
    blueprint = {
        "nodes": [
            {"id": "rand_float", "type": "math/random/random", "properties": {"Min": 1.5, "Max": 2.5, "IntegerMode": False}},
            {"id": "rand_int", "type": "math/random/random", "properties": {"Min": 10.0, "Max": 20.0, "IntegerMode": True}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    val_float = await engine.nodes["rand_float"].pull_data(context, "Value")
    assert 1.5 <= val_float <= 2.5
    
    val_int = await engine.nodes["rand_int"].pull_data(context, "Value")
    assert 10.0 <= val_int <= 20.0
    assert val_int == int(val_int)


@pytest.mark.asyncio
async def test_array_nodes():
    blueprint = {
        "nodes": [
            {"id": "arr_create", "type": "arrays/manipulation/create", "properties": {"CSVString": "10, 20, 30, test", "ParseNumbers": True}},
            {"id": "arr_len", "type": "arrays/operations/length", "properties": {}},
            {"id": "arr_get", "type": "arrays/operations/get", "properties": {"Index": 2}},
            {"id": "arr_concat", "type": "arrays/manipulation/concat", "properties": {"ArrayB": [40, 50]}}
        ],
        "links": [
            {"id": "l1", "type": "data", "source_node": "arr_create", "source_pin": "Array", "target_node": "arr_len", "target_pin": "Array"},
            {"id": "l2", "type": "data", "source_node": "arr_create", "source_pin": "Array", "target_node": "arr_get", "target_pin": "Array"},
            {"id": "l3", "type": "data", "source_node": "arr_create", "source_pin": "Array", "target_node": "arr_concat", "target_pin": "ArrayA"}
        ]
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    arr = await engine.nodes["arr_create"].pull_data(context, "Array")
    assert arr == [10, 20, 30, "test"]
    
    length = await engine.nodes["arr_len"].pull_data(context, "Length")
    assert length == 4

    item = await engine.nodes["arr_get"].pull_data(context, "Item")
    assert item == 30

    concat_res = await engine.nodes["arr_concat"].pull_data(context, "Result")
    assert concat_res == [10, 20, 30, "test", 40, 50]


@pytest.mark.asyncio
async def test_string_nodes():
    blueprint = {
        "nodes": [
            {"id": "str_concat", "type": "string/concat", "properties": {"A": "Hello", "B": "World", "Separator": " "}},
            {"id": "str_format", "type": "string/format", "properties": {"Template": "{0} equals {1}", "Arg0": "pi", "Arg1": 3.1415}},
            {"id": "str_case", "type": "string/case", "properties": {"InputString": "CoMfYlAb", "ToUppercase": False}}
        ],
        "links": []
    }
    engine = ExecutionEngine()
    engine.load_blueprint(blueprint)
    context = ExecutionContext(engine, "test_run", engine.lock_manager)
    
    concat = await engine.nodes["str_concat"].pull_data(context, "Result")
    assert concat == "Hello World"
    
    formatted = await engine.nodes["str_format"].pull_data(context, "Result")
    assert formatted == "pi equals 3.1415"

    cased = await engine.nodes["str_case"].pull_data(context, "Result")
    assert cased == "comfylab"
