from argparse import Namespace

from scripts.prepare_tcm_dataset_sft import DEFAULT_INSTRUCTION, normalize_record


def make_args(**overrides):
    defaults = {
        "min_input_chars": 4,
        "min_output_chars": 10,
        "max_input_chars": 2000,
        "max_output_chars": 6000,
        "allow_clinical_plan": False,
        "disable_tcm_keyword_filter": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_prepare_record_fills_default_instruction_for_tcm_qa() -> None:
    record, reason = normalize_record(
        {"instruction": "", "input": "银柴胡的主要功效是什么？", "output": "银柴胡的主要功效是清虚热，除疳热。"},
        make_args(),
    )

    assert reason == ""
    assert record is not None
    assert record["instruction"] == DEFAULT_INSTRUCTION


def test_prepare_record_filters_non_tcm_topic_before_default_instruction() -> None:
    record, reason = normalize_record(
        {"instruction": "", "input": "这句话如何翻译成英文？", "output": "This sentence can be translated into English."},
        make_args(),
    )

    assert record is None
    assert reason == "non_tcm_topic"


def test_prepare_record_filters_unsafe_clinical_plan() -> None:
    record, reason = normalize_record(
        {
            "instruction": "基于输入的患者医案记录，直接给出你认为的方剂中药组成。",
            "input": "病例信息: 乏力、口干、头晕。",
            "output": "柴胡12 黄芩10 生甘草9。",
        },
        make_args(),
    )

    assert record is None
    assert reason == "unsafe_clinical_plan"
