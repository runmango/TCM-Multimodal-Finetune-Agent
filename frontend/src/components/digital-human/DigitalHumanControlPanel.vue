<script setup lang="ts">
import type { DigitalHumanScene } from "@/types/digitalHuman";

defineProps<{
  loading: boolean;
}>();

const text = defineModel<string>("text", { required: true });
const scene = defineModel<DigitalHumanScene>("scene", { required: true });
const voice = defineModel<string>("voice", { required: true });
const modelUrl = defineModel<string>("modelUrl", { required: true });

const emit = defineEmits<{
  submit: [];
  clear: [];
}>();
</script>

<template>
  <section class="digital-human-control">
    <div class="control-heading">
      <h3>播报控制</h3>
      <p>粘贴体质问卷结果、知识问答结果或健康科普文本后播报。</p>
    </div>

    <el-form label-position="top">
      <el-form-item label="需要播报的内容">
        <el-input v-model="text" type="textarea" :rows="9" maxlength="1200" show-word-limit />
      </el-form-item>
      <el-form-item label="scene">
        <el-select v-model="scene" class="full-width">
          <el-option label="constitution_result" value="constitution_result" />
          <el-option label="knowledge_answer" value="knowledge_answer" />
          <el-option label="general_notice" value="general_notice" />
        </el-select>
      </el-form-item>
      <el-form-item label="播报音色">
        <el-input v-model="voice" placeholder="zh-CN-XiaoxiaoNeural" />
      </el-form-item>
      <el-form-item label="模型路径（可选）">
        <el-input v-model="modelUrl" placeholder="/models/doctor.vrm 或 /models/doctor.glb" clearable />
      </el-form-item>
      <div class="control-actions">
        <el-button type="primary" :loading="loading" @click="emit('submit')">开始播报</el-button>
        <el-button @click="emit('clear')">清空</el-button>
      </div>
    </el-form>
  </section>
</template>

<style scoped>
.digital-human-control {
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dceaf3;
  border-radius: 8px;
}

.control-heading {
  margin-bottom: 14px;
}

.control-heading h3 {
  margin: 0 0 6px;
  color: #10466f;
}

.control-heading p {
  margin: 0;
  color: #5c7282;
  line-height: 1.7;
}

.full-width {
  width: 100%;
}

.control-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
