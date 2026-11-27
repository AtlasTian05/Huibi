<script setup lang="ts">
import type { Submission } from '../types'
defineProps<{ result: Submission }>()
const labels: Record<string, string> = {
  content: '内容与任务',
  coherence: '结构与衔接',
  language: '词汇与表达',
  grammar: '语法与准确性',
}
</script>

<template>
  <article class="review-result" aria-labelledby="result-title">
    <div class="result-heading">
      <div>
        <p class="eyebrow">REVIEW</p>
        <h2 id="result-title">评阅结果</h2>
      </div>
      <span class="pill">{{ result.exam_type }}</span>
    </div>
    <p v-if="result.score_error" class="error" role="alert">
      评分未成功，已保留评阅反馈。
    </p>
    <p v-else-if="result.primary_score != null" class="score-line">
      <strong>{{ result.primary_score }}</strong
      ><span
        >/ {{ result.primary_max }}<br /><small>{{
          result.primary_label
        }}</small></span
      >
    </p>
    <p class="muted small">公开量表 · AI 模拟评分 · 非官方成绩</p>
    <p v-if="result.overall_summary" class="summary-text">
      {{ result.overall_summary }}
    </p>
    <table
      v-if="Object.keys(result.score_details || {}).length"
      class="rubric-table"
    >
      <caption>
        维度得分
      </caption>
      <tbody>
        <tr v-for="(score, label) in result.score_details" :key="label">
          <th scope="row">{{ label }}</th>
          <td>{{ score }}</td>
        </tr>
      </tbody>
    </table>
    <details v-if="result.essay_text">
      <summary>作文原文</summary>
      <p class="essay-text">{{ result.essay_text }}</p>
    </details>
    <details v-if="result.image_analysis">
      <summary>题图理解</summary>
      <img
        v-if="result.image_url"
        class="result-image"
        :src="result.image_url"
        alt="本次雅思 Task 1 题图"
      />
      <p class="pre-wrap">{{ result.image_analysis }}</p>
    </details>
    <div
      v-if="Object.keys(result.feedback_dimensions || {}).length"
      class="feedback-grid"
    >
      <section
        v-for="(dimension, key) in result.feedback_dimensions"
        :key="key"
        class="feedback-card"
      >
        <h3>{{ labels[key] || key }}</h3>
        <p><span class="feedback-label">优势</span>{{ dimension.strengths }}</p>
        <p>
          <span class="feedback-label">改进</span>{{ dimension.improvements }}
        </p>
        <div
          v-for="(tip, index) in dimension.tips || []"
          :key="index"
          class="feedback-tip"
        >
          <h4>{{ tip.title }}</h4>
          <p>{{ tip.comment }}</p>
          <blockquote v-if="tip.example">{{ tip.example }}</blockquote>
        </div>
      </section>
    </div>
    <p v-else class="pre-wrap">
      {{ result.qualitative_feedback || '本次未获得定性反馈，请稍后重试。' }}
    </p>
    <section
      v-if="result.coach_plan?.action_items?.length"
      class="coach-section"
    >
      <h3>修改清单</h3>
      <ol>
        <li
          v-for="(item, index) in result.coach_plan.action_items"
          :key="index"
        >
          <strong>{{ item.title }}</strong>
          <p>{{ item.detail }}</p>
        </li>
      </ol>
    </section>
    <section v-if="result.coach_plan?.exercises?.length" class="coach-section">
      <h3>专项练习</h3>
      <article
        v-for="(exercise, index) in result.coach_plan.exercises"
        :key="index"
      >
        <h4>{{ exercise.title }}</h4>
        <p>{{ exercise.instruction }}</p>
      </article>
    </section>
    <details v-if="result.coach_plan?.model_essay?.text">
      <summary>AI 参考范文 · {{ result.coach_plan.model_essay.title }}</summary>
      <p class="muted small">AI 生成 · 非官方范文或真实考生作品</p>
      <p class="essay-text">{{ result.coach_plan.model_essay.text }}</p>
      <ul>
        <li
          v-for="(highlight, index) in result.coach_plan.model_essay.highlights"
          :key="index"
        >
          {{ highlight }}
        </li>
      </ul>
    </details>
    <p v-else-if="result.revision_plan" class="pre-wrap">
      {{ result.revision_plan }}
    </p>
  </article>
</template>
