<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { DataAnalysis, Picture, Service, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage, type UploadProps } from "element-plus";

import {
  getQuestionnaire,
  submitQuestionnaire,
  uploadTongueImage,
  type QuestionnaireResponse,
  type QuestionnaireSubmitResponse,
  type TongueFeatures,
} from "@/api/constitutionQuestionnaire";
import { normalizeBaseUrl, type ApiFriendlyError } from "@/api/tcmApi";
import SafetyNotice from "@/components/SafetyNotice.vue";

const props = defineProps<{
  apiBaseUrl: string;
}>();

const SAFETY_NOTICE = "仅供健康科普参考，不替代医生诊疗。";
const router = useRouter();

const loadingQuestionnaire = ref(false);
const submitting = ref(false);
const uploadingTongue = ref(false);
const voice = ref("zh-CN-XiaoxiaoNeural");
const gender = ref<"unknown" | "male" | "female">("unknown");
const questionnaire = ref<QuestionnaireResponse | null>(null);
const result = ref<QuestionnaireSubmitResponse | null>(null);
const error = ref<ApiFriendlyError | null>(null);
const answers = reactive<Record<string, number>>({});
const tongueImageUrl = ref<string | null>(null);
const tongueFileName = ref("");
const teethMarks = ref<"unknown" | "yes" | "no">("unknown");
const tongueFeatures = reactive<TongueFeatures>({
  tongue_color: null,
  tongue_coating: null,
  teeth_marks: null,
  tongue_shape: null,
});

const tongueColorOptions = ["淡红", "淡", "红", "暗红"];
const tongueCoatingOptions = ["薄白", "白腻", "黄腻", "少苔"];
const tongueShapeOptions = ["正常", "胖大", "瘦薄"];

const questions = computed(() => questionnaire.value?.questions || []);
const visibleQuestions = computed(() =>
  questions.value.filter((question) => !question.applies_to || question.applies_to === gender.value),
);
const options = computed(() => questionnaire.value?.options || []);
const totalQuestionCount = computed(() => visibleQuestions.value.length);
const completedQuestionCount = computed(
  () => visibleQuestions.value.filter((question) => answers[question.id] !== undefined && answers[question.id] !== null).length,
);
const missingCount = computed(() => totalQuestionCount.value - completedQuestionCount.value);
const sortedScores = computed(() =>
  Object.entries(result.value?.scores || {}).sort((a, b) => b[1] - a[1]),
);
const judgementEntries = computed(() => Object.entries(result.value?.constitution_judgements || {}));
const tonguePreviewUrl = computed(() => resolveBackendAssetUrl(tongueImageUrl.value));
const fourDiagnosisJson = computed(() => JSON.stringify(result.value?.four_diagnosis || {}, null, 2));

onMounted(loadQuestionnaire);

async function loadQuestionnaire() {
  loadingQuestionnaire.value = true;
  error.value = null;
  try {
    questionnaire.value = await getQuestionnaire(props.apiBaseUrl);
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    loadingQuestionnaire.value = false;
  }
}

const beforeTongueUpload: UploadProps["beforeUpload"] = async (rawFile) => {
  if (!["image/jpeg", "image/png", "image/webp"].includes(rawFile.type)) {
    ElMessage.warning("仅支持 jpg、jpeg、png、webp 舌象图片。");
    return false;
  }
  if (rawFile.size > 5 * 1024 * 1024) {
    ElMessage.warning("图片大小不能超过 5MB。");
    return false;
  }

  uploadingTongue.value = true;
  error.value = null;
  try {
    const uploadResult = await uploadTongueImage(rawFile, props.apiBaseUrl);
    tongueImageUrl.value = uploadResult.url;
    tongueFileName.value = uploadResult.filename;
    ElMessage.success("舌象图片上传成功。");
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    uploadingTongue.value = false;
  }
  return false;
};

function clearTongueImage() {
  tongueImageUrl.value = null;
  tongueFileName.value = "";
}

async function submit() {
  if (missingCount.value > 0) {
    ElMessage.warning("请完成全部问卷题目后再提交。");
    return;
  }

  submitting.value = true;
  error.value = null;
  result.value = null;
  try {
    const payload = visibleQuestions.value.map((question) => ({
      question_id: question.id,
      score: answers[question.id],
    }));
    result.value = await submitQuestionnaire(
      {
        answers: payload,
        tongue_image_url: tongueImageUrl.value,
        tongue_features: buildTongueFeaturePayload(),
        top_k: 3,
        gender: gender.value,
      },
      props.apiBaseUrl,
    );
  } catch (err) {
    error.value = err as ApiFriendlyError;
  } finally {
    submitting.value = false;
  }
}

async function speakResult() {
  const speakText = result.value?.broadcast_text || result.value?.result_text;
  if (!speakText) return;
  localStorage.setItem("digital_human_speak_text", speakText);
  localStorage.setItem("digital_human_scene", "constitution_result");
  localStorage.setItem("digital_human_voice", voice.value);
  void router.push("/digital-human");
}

function buildTongueFeaturePayload(): TongueFeatures | null {
  const payload: TongueFeatures = {
    tongue_color: tongueFeatures.tongue_color || null,
    tongue_coating: tongueFeatures.tongue_coating || null,
    teeth_marks: teethMarks.value === "unknown" ? null : teethMarks.value === "yes",
    tongue_shape: tongueFeatures.tongue_shape || null,
  };
  const hasValue = Object.values(payload).some((value) => value !== null && value !== undefined && value !== "");
  return hasValue ? payload : null;
}

function resolveBackendAssetUrl(path: string | null | undefined): string {
  const value = (path || "").trim();
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${normalizeBaseUrl(props.apiBaseUrl)}${value.startsWith("/") ? value : `/${value}`}`;
}

function judgementType(judgement: string): "success" | "warning" | "info" | "danger" {
  if (judgement === "是" || judgement === "基本是") return "success";
  if (judgement === "倾向是") return "warning";
  if (judgement === "信息不足") return "info";
  return "danger";
}
</script>

<template>
  <section class="tool-surface">
    <div class="view-heading">
      <div>
        <h2>体质辨识问卷</h2>
        <p>通过正式转化分算法、四诊结构化数据和向量 RAG 知识库解释生成演示闭环。</p>
      </div>
      <el-tag size="large" effect="light">GB/T46939-2025</el-tag>
    </div>

    <SafetyNotice />

    <el-alert
      title="体质评分采用《中医体质分类与判定》转化分算法，系统结果仅用于体质倾向分析和健康管理参考，不能替代医生诊断。"
      type="info"
      :closable="false"
      show-icon
    />
  </section>

  <el-alert v-if="error" class="page-alert" :title="error.message" type="warning" :closable="false" show-icon>
    <el-collapse class="error-detail">
      <el-collapse-item title="技术详情" name="error">
        <pre>{{ JSON.stringify(error, null, 2) }}</pre>
      </el-collapse-item>
    </el-collapse>
  </el-alert>

  <section class="tool-surface">
    <div class="questionnaire-toolbar">
      <div>
        <h3>可选上传舌象图片</h3>
        <p>第一版不做真实舌象识别，上传图片和人工标签会进入四诊结构化 JSON。</p>
      </div>
      <el-upload
        class="tongue-upload"
        accept="image/jpeg,image/png,image/webp"
        :show-file-list="false"
        :before-upload="beforeTongueUpload"
      >
        <el-button type="primary" plain :loading="uploadingTongue" :icon="UploadFilled">上传舌象图片</el-button>
      </el-upload>
    </div>

    <div class="tongue-grid">
      <div class="tongue-preview">
        <img v-if="tonguePreviewUrl" :src="tonguePreviewUrl" alt="舌象图片预览" />
        <div v-else class="tongue-preview__empty">
          <el-icon><Picture /></el-icon>
          <span>未上传舌象图片</span>
        </div>
        <div v-if="tongueFileName" class="tongue-preview__meta">
          <span>{{ tongueFileName }}</span>
          <el-button link type="primary" @click="clearTongueImage">移除</el-button>
        </div>
      </div>

      <el-form label-position="top" class="tongue-feature-form">
        <el-form-item label="舌质">
          <el-select v-model="tongueFeatures.tongue_color" clearable placeholder="未选择">
            <el-option v-for="option in tongueColorOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
        <el-form-item label="舌苔">
          <el-select v-model="tongueFeatures.tongue_coating" clearable placeholder="未选择">
            <el-option v-for="option in tongueCoatingOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
        <el-form-item label="齿痕">
          <el-radio-group v-model="teethMarks">
            <el-radio-button value="unknown">未选择</el-radio-button>
            <el-radio-button value="yes">有</el-radio-button>
            <el-radio-button value="no">无</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="舌形">
          <el-select v-model="tongueFeatures.tongue_shape" clearable placeholder="未选择">
            <el-option v-for="option in tongueShapeOptions" :key="option" :label="option" :value="option" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
  </section>

  <section class="tool-surface">
    <div class="questionnaire-toolbar">
      <div>
        <h3>问卷题目</h3>
        <p>当前共 {{ totalQuestionCount }} 道题，已完成 {{ completedQuestionCount }} 道。</p>
      </div>
      <el-button :loading="loadingQuestionnaire" @click="loadQuestionnaire">刷新问卷</el-button>
    </div>

    <el-form label-position="top" class="gender-form">
      <el-form-item label="性别相关题目">
        <el-radio-group v-model="gender">
          <el-radio-button value="unknown">不选择</el-radio-button>
          <el-radio-button value="male">男性</el-radio-button>
          <el-radio-button value="female">女性</el-radio-button>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <el-skeleton v-if="loadingQuestionnaire" :rows="6" animated />
    <div v-else class="question-list">
      <div v-for="(question, index) in visibleQuestions" :key="question.id" class="question-card">
        <div class="question-card__title">
          <strong>{{ index + 1 }}. {{ question.text }}</strong>
          <el-tag effect="plain">{{ question.constitution }}</el-tag>
          <el-tag v-if="question.applies_to" type="warning" effect="plain">
            {{ question.applies_to === "male" ? "男性题" : "女性题" }}
          </el-tag>
        </div>
        <el-radio-group v-model="answers[question.id]" class="option-row">
          <el-radio-button v-for="option in options" :key="option.score" :value="option.score">
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
      <el-empty v-if="questions.length === 0" description="暂无问卷题目，请确认后端接口已启动" />
    </div>

    <div class="form-actions questionnaire-actions">
      <el-form-item label="播报音色">
        <el-input v-model="voice" class="voice-input" />
      </el-form-item>
      <el-button type="primary" size="large" :icon="DataAnalysis" :loading="submitting" @click="submit">
        提交问卷并生成闭环结果
      </el-button>
    </div>
  </section>

  <section v-if="result" class="result-section">
    <div class="summary-grid">
      <div class="summary-card accent">
        <span>主要体质倾向</span>
        <strong>{{ result.primary_constitution }}</strong>
      </div>
      <div class="summary-card">
        <span>兼夹体质</span>
        <strong>{{ result.secondary_constitutions.length ? result.secondary_constitutions.join("、") : "无明显兼夹" }}</strong>
      </div>
      <div class="summary-card">
        <span>算法版本</span>
        <strong>{{ result.algorithm_version }}</strong>
      </div>
      <div class="summary-card">
        <span>记录 ID</span>
        <strong>{{ result.session_id }}</strong>
      </div>
      <div class="summary-card">
        <span>RAG 检索</span>
        <strong>{{ result.retriever_type }}</strong>
      </div>
    </div>

    <section class="tool-surface">
      <h3>分析结论与调养建议</h3>
      <el-alert :title="result.result_text" type="success" :closable="false" show-icon />
      <div class="question-actions">
        <el-button type="primary" plain :icon="Service" @click="speakResult">
          让数字人播报问卷结果
        </el-button>
      </div>
    </section>

    <section class="tool-surface">
      <h3>四诊结构化数据</h3>
      <pre class="json-box">{{ fourDiagnosisJson }}</pre>
    </section>

    <section class="tool-surface">
      <h3>向量 RAG 知识库解释</h3>
      <el-alert :title="result.rag_explanation" type="info" :closable="false" show-icon />
      <div v-if="result.rag_sources.length" class="source-list">
        <el-card v-for="source in result.rag_sources" :key="source.source_id" class="result-card" shadow="never">
          <template #header>
            <div class="result-card__header">
              <div class="result-card__title">{{ source.title || "未命名来源" }}</div>
              <el-tag effect="light">{{ source.source_type }}</el-tag>
            </div>
          </template>
          <div class="result-card__meta">
            <span>ID：{{ source.source_id }}</span>
            <span>score：{{ source.score ?? "-" }}</span>
          </div>
        </el-card>
      </div>
      <el-empty v-else description="未命中本地知识来源，已展示安全兜底解释" />
    </section>

    <section class="tool-surface">
      <h3>数字人播报文本</h3>
      <el-alert :title="result.broadcast_text" type="success" :closable="false" show-icon />
      <div class="question-actions">
        <el-button type="primary" :icon="Service" @click="speakResult">进入数字人播报页</el-button>
      </div>
    </section>

    <section class="tool-surface">
      <h3>九种体质转化分与判定</h3>
      <div class="score-list">
        <div v-for="[name, score] in sortedScores" :key="name" class="score-row">
          <span>{{ name }}</span>
          <el-progress :percentage="score" :stroke-width="12" />
          <el-tag :type="judgementType(result.constitution_judgements[name] || '信息不足')" effect="light">
            {{ result.constitution_judgements[name] || "信息不足" }}
          </el-tag>
        </div>
      </div>
      <div class="judgement-list">
        <el-tag
          v-for="[name, judgement] in judgementEntries"
          :key="name"
          :type="judgementType(judgement)"
          effect="plain"
        >
          {{ name }}：{{ judgement }}
        </el-tag>
      </div>
    </section>
  </section>

  <SafetyNotice :text="result?.safety_notice || SAFETY_NOTICE" />
</template>

<style scoped>
.questionnaire-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  margin-bottom: 16px;
}

.questionnaire-toolbar h3 {
  margin: 0 0 4px;
}

.tongue-grid {
  display: grid;
  grid-template-columns: minmax(240px, 320px) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.tongue-preview {
  min-height: 220px;
  overflow: hidden;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.tongue-preview img {
  display: block;
  width: 100%;
  height: 220px;
  object-fit: contain;
  background: #ffffff;
}

.tongue-preview__empty {
  display: grid;
  place-items: center;
  height: 220px;
  color: #6d8494;
  gap: 8px;
}

.tongue-preview__empty .el-icon {
  font-size: 34px;
  color: #1f78b4;
}

.tongue-preview__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid #dceaf3;
  color: #5c7282;
  font-size: 13px;
}

.tongue-feature-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px 16px;
}

.tongue-feature-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.question-list {
  display: grid;
  gap: 12px;
}

.question-card {
  padding: 14px;
  background: #f7fbff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.question-card__title {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
  color: #10466f;
}

.question-card__title strong {
  flex: 1;
  color: #10466f;
  font-weight: 700;
}

.option-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.questionnaire-actions {
  margin-top: 18px;
}

.gender-form {
  margin-bottom: 14px;
}

.voice-input {
  width: 240px;
}

.question-actions {
  margin-top: 14px;
}

.source-list {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.score-list {
  display: grid;
  gap: 12px;
}

.score-row {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr) 88px;
  gap: 12px;
  align-items: center;
}

.score-row span {
  color: #10466f;
  font-weight: 700;
}

.judgement-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

@media (max-width: 760px) {
  .questionnaire-toolbar,
  .score-row,
  .tongue-grid {
    grid-template-columns: 1fr;
  }

  .questionnaire-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
