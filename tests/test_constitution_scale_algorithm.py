from app.services.constitution_scale_service import (
    ALGORITHM_VERSION,
    reverse_score,
    score_constitution_scale,
    transformation_score,
)


def test_transformation_score_formula() -> None:
    assert transformation_score(raw_score=15, item_count=3) == 100.0
    assert transformation_score(raw_score=9, item_count=4) == 31.2


def test_reverse_score() -> None:
    assert reverse_score(1) == 5
    assert reverse_score(2) == 4
    assert reverse_score(3) == 3
    assert reverse_score(4) == 2
    assert reverse_score(5) == 1


def test_pinghe_judgement_can_be_yes() -> None:
    result = score_constitution_scale(
        [
            {"question_id": "balanced_energy", "score": 5},
            {"question_id": "regular_routine", "score": 5},
            {"question_id": "stable_mood", "score": 5},
            {"question_id": "fatigue", "score": 1},
            {"question_id": "shortness_of_breath", "score": 1},
        ]
    )

    assert result["algorithm_version"] == ALGORITHM_VERSION
    assert result["constitution_judgements"]["平和质"] == "是"
    assert result["primary_constitution"] == "平和质"


def test_bias_constitution_yes_tendency_and_no() -> None:
    yes_result = score_constitution_scale(
        [
            {"question_id": "fatigue", "score": 5},
            {"question_id": "shortness_of_breath", "score": 5},
            {"question_id": "spontaneous_sweating", "score": 4},
            {"question_id": "easy_cold", "score": 4},
        ]
    )
    assert yes_result["constitution_judgements"]["气虚质"] == "是"
    assert yes_result["primary_constitution"] == "气虚质"

    tendency_result = score_constitution_scale(
        [
            {"question_id": "fatigue", "score": 3},
            {"question_id": "shortness_of_breath", "score": 2},
            {"question_id": "spontaneous_sweating", "score": 2},
            {"question_id": "easy_cold", "score": 2},
        ]
    )
    assert tendency_result["constitution_judgements"]["气虚质"] == "倾向是"
    assert tendency_result["primary_constitution"] == "气虚质（倾向）"

    no_result = score_constitution_scale(
        [
            {"question_id": "fatigue", "score": 1},
            {"question_id": "shortness_of_breath", "score": 1},
            {"question_id": "spontaneous_sweating", "score": 1},
            {"question_id": "easy_cold", "score": 1},
        ]
    )
    assert no_result["constitution_judgements"]["气虚质"] == "否"


def test_empty_answers_return_information_insufficient() -> None:
    result = score_constitution_scale([])

    assert result["primary_constitution"] == "信息不足"
    assert set(result["constitution_judgements"].values()) == {"信息不足"}
