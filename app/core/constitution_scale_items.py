from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


ALGORITHM_VERSION = "GB/T46939-2025"

CONSTITUTIONS = [
    "平和质",
    "气虚质",
    "阳虚质",
    "阴虚质",
    "痰湿质",
    "湿热质",
    "血瘀质",
    "气郁质",
    "特禀质",
]

BIAS_CONSTITUTIONS = [constitution for constitution in CONSTITUTIONS if constitution != "平和质"]


@dataclass(frozen=True)
class ScaleItem:
    id: str
    text: str
    constitution: str
    reverse: bool = False
    inquiry_field: Optional[str] = None
    applies_to: Optional[str] = None
    legacy_id: Optional[str] = None
    answer_id: Optional[str] = None


SCALE_ITEMS = [
    ScaleItem("balanced_energy", "您精力充沛吗？", "平和质", inquiry_field="sleep_quality", legacy_id="q001"),
    ScaleItem("regular_routine", "您睡眠、饮食和排便总体规律吗？", "平和质", inquiry_field="diet_regular", legacy_id="q002"),
    ScaleItem("stable_mood", "您平时情绪比较稳定、适应力较好吗？", "平和质", inquiry_field="mood_stability", legacy_id="q003"),
    ScaleItem("pinghe_fatigue_reverse", "您容易疲乏吗？", "平和质", reverse=True, inquiry_field="fatigue", answer_id="fatigue"),
    ScaleItem(
        "pinghe_shortness_reverse",
        "您容易气短、懒得说话吗？",
        "平和质",
        reverse=True,
        inquiry_field="shortness_of_breath",
        answer_id="shortness_of_breath",
    ),
    ScaleItem("fatigue", "您容易疲乏吗？", "气虚质", inquiry_field="fatigue", legacy_id="q004"),
    ScaleItem("shortness_of_breath", "您容易气短、懒得说话吗？", "气虚质", inquiry_field="shortness_of_breath", legacy_id="q005"),
    ScaleItem("spontaneous_sweating", "您稍微活动后容易出汗吗？", "气虚质", inquiry_field="spontaneous_sweating", legacy_id="q006"),
    ScaleItem("easy_cold", "您平时容易感冒或抵抗力偏弱吗？", "气虚质", inquiry_field="easy_cold"),
    ScaleItem("cold_limbs", "您手脚发凉吗？", "阳虚质", inquiry_field="cold_intolerance", legacy_id="q007"),
    ScaleItem("cold_intolerance", "您比一般人怕冷吗？", "阳虚质", inquiry_field="cold_intolerance", legacy_id="q008"),
    ScaleItem("prefers_warm_food", "您偏爱热饮或温热食物吗？", "阳虚质", inquiry_field="cold_intolerance", legacy_id="q009"),
    ScaleItem("loose_stool", "您容易大便偏稀或腹部怕冷吗？", "阳虚质", inquiry_field="stool_regular"),
    ScaleItem("dry_mouth", "您经常口干、咽干吗？", "阴虚质", legacy_id="q010"),
    ScaleItem("night_sweating", "您夜间容易盗汗吗？", "阴虚质", legacy_id="q011"),
    ScaleItem("vexing_heat", "您容易出现手足心热或心烦感吗？", "阴虚质", legacy_id="q012"),
    ScaleItem("dry_stool", "您容易大便干结吗？", "阴虚质"),
    ScaleItem("heavy_body", "您常觉得身体沉重、困倦吗？", "痰湿质", legacy_id="q013"),
    ScaleItem("phlegm_sticky", "您容易痰多或咽中黏腻吗？", "痰湿质", legacy_id="q014"),
    ScaleItem("greasy_coating", "您腹部偏肥满或舌苔偏厚腻吗？", "痰湿质", legacy_id="q015"),
    ScaleItem("oily_face", "您面部容易油腻或出汗黏腻吗？", "痰湿质"),
    ScaleItem("bitter_mouth", "您经常口苦、口黏吗？", "湿热质", legacy_id="q016"),
    ScaleItem("yellow_urine", "您小便颜色偏黄吗？", "湿热质", legacy_id="q017"),
    ScaleItem("oily_skin_acne", "您皮肤容易出油、长痘或有湿疹样不适吗？", "湿热质", legacy_id="q018"),
    ScaleItem("male_scrotal_dampness", "男性是否容易阴囊潮湿？", "湿热质", applies_to="male"),
    ScaleItem("female_leucorrhea_yellow", "女性是否容易带下色黄或黏腻？", "湿热质", applies_to="female"),
    ScaleItem("dark_complexion_lips", "您面色或唇色容易偏暗吗？", "血瘀质", legacy_id="q019"),
    ScaleItem("fixed_stabbing_pain", "您身体某些部位容易出现固定刺痛吗？", "血瘀质", legacy_id="q020"),
    ScaleItem("purple_tongue", "您舌色偏紫暗或容易有瘀斑吗？", "血瘀质", legacy_id="q021"),
    ScaleItem("skin_bruise", "您皮肤容易出现瘀斑或色素沉着吗？", "血瘀质"),
    ScaleItem("low_mood", "您容易情绪低落、闷闷不乐吗？", "气郁质", legacy_id="q022"),
    ScaleItem("chest_hypochondriac_distension", "您常觉得胸胁胀满或咽中有异物感吗？", "气郁质", legacy_id="q023"),
    ScaleItem("frequent_sighing", "您平时容易叹气吗？", "气郁质", legacy_id="q024"),
    ScaleItem("poor_sleep", "您情绪波动时容易睡眠不安吗？", "气郁质", inquiry_field="sleep_quality"),
    ScaleItem("allergy", "您容易过敏吗？", "特禀质", legacy_id="q025"),
    ScaleItem("rhinitis_asthma_sensitive_skin", "您有反复鼻炎、哮喘或皮肤敏感倾向吗？", "特禀质", legacy_id="q026"),
    ScaleItem("environment_food_drug_sensitivity", "您接触某些食物、药物或环境后容易不适吗？", "特禀质", legacy_id="q027"),
    ScaleItem("urticaria_eczema", "您是否容易出现荨麻疹或反复皮肤瘙痒？", "特禀质"),
]

SCALE_ITEM_BY_ID = {item.id: item for item in SCALE_ITEMS}
LEGACY_TO_SCALE_ID = {item.legacy_id: item.id for item in SCALE_ITEMS if item.legacy_id}

QUESTION_ID_ALIASES = {
    **LEGACY_TO_SCALE_ID,
    "tired": "fatigue",
    "qi_shortage": "shortness_of_breath",
    "sweating": "spontaneous_sweating",
}
