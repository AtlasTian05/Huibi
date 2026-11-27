<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { api, ApiError, post } from '../api'
import { user } from '../auth'
import {
  EXAMS,
  IELTS_TASK1,
  IELTS_TASK2,
  TOEFL_TASKS,
  type Exam,
  type Submission,
} from '../types'
import ReviewResult from './ReviewResult.vue'
import ScoreHistory from './ScoreHistory.vue'
const router = useRouter()
const tab = ref<'write' | 'history' | 'knowledge'>('write')
const exam = ref<Exam>(EXAMS[0])
const subtype = ref('')
const topic = ref('')
const essay = ref('')
const image = ref<{ base64: string; mime: string; name: string } | null>(null)
const imageBusy = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const busy = ref(false)
const error = ref('')
const result = ref<Submission | null>(null)
const records = ref<Submission[]>([])
const historyBusy = ref(false)
const historyLoaded = ref(false)
const historyError = ref('')
const deleteTarget = ref<number | null>(null)
const deleteBusy = ref(false)
const question = ref('')
const answer = ref('')
const qaBusy = ref(false)
const qaError = ref('')
const wordCount = computed(() =>
  essay.value.trim() ? essay.value.trim().split(/\s+/).length : 0,
)
const canSubmit = computed(
  () =>
    wordCount.value >= 20 &&
    wordCount.value <= 1000 &&
    !busy.value &&
    !imageBusy.value,
)
const showUpload = computed(
  () => exam.value === EXAMS[1] && subtype.value === IELTS_TASK1,
)
const subtypes = computed(() =>
  exam.value === EXAMS[1]
    ? [IELTS_TASK2, IELTS_TASK1]
    : exam.value === EXAMS[2]
      ? TOEFL_TASKS
      : [],
)
watch(exam, () => {
  subtype.value = subtypes.value[0] || ''
  clearImage()
})
watch(subtype, () => {
  clearImage()
})
watch(tab, async (value) => {
  error.value = ''
  if (value === 'history' && !historyLoaded.value) await loadHistory()
})
onBeforeRouteLeave(
  () =>
    (!busy.value && !qaBusy.value) || window.confirm('任务进行中，确认离开？'),
)

async function handleError(e: unknown) {
  if (e instanceof ApiError && e.status === 401) {
    user.value = null
    await router.push('/login')
  }
  return (e as Error).message
}
function clearImage() {
  image.value = null
  if (fileInput.value) fileInput.value.value = ''
}
async function upload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  error.value = ''
  image.value = null
  if (
    !['image/png', 'image/jpeg', 'image/webp'].includes(file.type) ||
    file.size > 5 * 1024 * 1024
  ) {
    error.value = '请选择 5 MB 以内的 PNG、JPEG 或 WebP 图片。'
    clearImage()
    return
  }
  imageBusy.value = true
  // Capture task identity so switching exam while FileReader runs cannot attach a stale image.
  const task = subtype.value
  try {
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result).split(',')[1])
      reader.onerror = () => reject(new Error('图片读取失败，请重试。'))
      reader.readAsDataURL(file)
    })
    if (showUpload.value && subtype.value === task)
      image.value = { base64, mime: file.type, name: file.name }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    imageBusy.value = false
  }
}
async function submit() {
  if (!canSubmit.value) return
  busy.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await post<Submission>('/reviews', {
      essay_text: essay.value,
      exam_type: exam.value,
      exam_subtype: subtype.value || null,
      essay_topic: topic.value,
      essay_image_b64: image.value?.base64 || null,
      essay_image_mime: image.value?.mime || null,
    })
    historyLoaded.value = false
  } catch (e) {
    error.value = await handleError(e)
  } finally {
    busy.value = false
  }
}
async function loadHistory() {
  historyBusy.value = true
  historyError.value = ''
  try {
    records.value = await api<Submission[]>('/submissions')
    historyLoaded.value = true
  } catch (e) {
    historyError.value = await handleError(e)
  } finally {
    historyBusy.value = false
  }
}
async function deleteRecord() {
  if (deleteTarget.value === null) return
  deleteBusy.value = true
  try {
    await api(`/submissions/${deleteTarget.value}`, { method: 'DELETE' })
    records.value = records.value.filter((row) => row.id !== deleteTarget.value)
    if (result.value?.id === deleteTarget.value) result.value = null
    deleteTarget.value = null
  } catch (e) {
    historyError.value = await handleError(e)
  } finally {
    deleteBusy.value = false
  }
}
async function ask() {
  if (!question.value.trim() || qaBusy.value) return
  qaBusy.value = true
  qaError.value = ''
  answer.value = ''
  try {
    answer.value = (
      await post<{ answer: string }>('/questions', {
        question: question.value,
        exam_type: exam.value,
      })
    ).answer
  } catch (e) {
    qaError.value = await handleError(e)
  } finally {
    qaBusy.value = false
  }
}
onMounted(() => {
  document.title = '创作工作台 · 慧笔 HuiBi'
})
</script>

<template>
  <div class="studio-shell">
    <section class="studio-heading">
      <div>
        <p class="eyebrow">HUIBI / WRITING STUDIO</p>
        <h1>写作工作台</h1>
      </div>
    </section>
    <div class="studio-content">
      <div class="studio-tabs" role="tablist" aria-label="工作台功能">
        <button
          id="tab-write"
          role="tab"
          aria-controls="panel-write"
          :aria-selected="tab === 'write'"
          @click="tab = 'write'"
        >
          写作 <span>01</span></button
        ><button
          id="tab-history"
          role="tab"
          aria-controls="panel-history"
          :aria-selected="tab === 'history'"
          @click="tab = 'history'"
        >
          档案 <span>02</span></button
        ><button
          id="tab-knowledge"
          role="tab"
          aria-controls="panel-knowledge"
          :aria-selected="tab === 'knowledge'"
          @click="tab = 'knowledge'"
        >
          问答 <span>03</span>
        </button>
      </div>

      <section
        v-show="tab === 'write'"
        id="panel-write"
        role="tabpanel"
        aria-labelledby="tab-write"
      >
        <form class="writing-layout" @submit.prevent="submit">
          <aside class="writing-settings">
            <h2>写作设置</h2>
            <label for="exam">写作类型</label
            ><select id="exam" v-model="exam" :disabled="busy">
              <option v-for="option in EXAMS" :key="option">
                {{ option }}
              </option></select
            ><template v-if="subtypes.length"
              ><label for="subtype">任务类型</label
              ><select id="subtype" v-model="subtype" :disabled="busy">
                <option v-for="option in subtypes" :key="option">
                  {{ option }}
                </option>
              </select></template
            ><label for="topic">题目 <span class="optional">选填</span></label
            ><textarea
              id="topic"
              v-model="topic"
              rows="4"
              maxlength="2000"
              :disabled="busy"
              placeholder=""
            ></textarea>
            <div v-if="showUpload" class="upload-section">
              <label for="chart"
                >Task 1 题图 <span class="optional">选填</span></label
              ><input
                id="chart"
                ref="fileInput"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                :disabled="busy || imageBusy"
                @change="upload"
              /><small>PNG / JPEG / WebP · 最大 5 MB</small>
              <div v-if="image" class="image-preview">
                <img
                  :src="`data:${image.mime};base64,${image.base64}`"
                  alt="待提交的 Task 1 题图"
                /><span>{{ image.name }}</span
                ><button
                  type="button"
                  class="text-button"
                  :disabled="busy"
                  @click="clearImage"
                >
                  移除图片
                </button>
              </div>
            </div>
          </aside>
          <div class="writing-editor">
            <div class="editor-title">
              <label for="essay">英文作文</label
              ><span :class="{ 'word-warning': wordCount > 1000 }"
                >{{ wordCount }} / 1000 词</span
              >
            </div>
            <textarea
              id="essay"
              v-model="essay"
              lang="en"
              spellcheck="true"
              :disabled="busy"
              maxlength="20000"
              placeholder=""
              aria-describedby="essay-help"
            ></textarea>
            <div class="editor-bottom">
              <p id="essay-help">20–1000 词</p>
              <button class="button dark" :disabled="!canSubmit">
                {{ busy ? '评阅中…' : '开始评阅' }}
                <span v-if="!busy" aria-hidden="true">↗</span>
              </button>
            </div>
          </div>
        </form>
        <div v-if="busy" class="processing" role="status" aria-live="polite">
          <span class="spinner"></span>
          <div>
            <strong>评阅中…</strong>
          </div>
        </div>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <ReviewResult v-if="result" :result="result" />
      </section>

      <section
        v-show="tab === 'history'"
        id="panel-history"
        role="tabpanel"
        aria-labelledby="tab-history"
        class="history-panel"
      >
        <div class="panel-heading">
          <div>
            <p class="eyebrow">ARCHIVE</p>
            <h2>写作档案</h2>
          </div>
          <button
            class="text-button"
            :disabled="historyBusy"
            @click="loadHistory"
          >
            刷新 ↻
          </button>
        </div>
        <p v-if="historyBusy" role="status">加载中…</p>
        <p v-if="historyError" class="error" role="alert">{{ historyError }}</p>
        <div
          v-if="!historyBusy && !records.length && !historyError"
          class="empty-state"
        >
          <span aria-hidden="true">↗</span>
          <h3>暂无记录</h3>
          <button class="button dark" @click="tab = 'write'">开始写作</button>
        </div>
        <ScoreHistory :records="records" />
        <div v-if="records.length" class="history-list">
          <article
            v-for="record in records"
            :key="record.id"
            class="history-row"
          >
            <div>
              <span class="eyebrow"
                >{{ record.exam_type }} ·
                {{
                  new Date(record.created_at || '').toLocaleDateString('zh-CN')
                }}</span
              >
              <h3>{{ record.essay_topic || '未命名练习' }}</h3>
              <p>
                {{
                  record.primary_score == null
                    ? '暂无可用评分'
                    : `${record.primary_score} / ${record.primary_max}`
                }}
                · {{ record.exam_subtype || '通用写作' }}
              </p>
            </div>
            <div class="history-actions">
              <button class="text-button" @click="result = record">
                查看反馈 ↗</button
              ><button
                class="text-button danger"
                @click="deleteTarget = record.id!"
              >
                删除
              </button>
            </div>
          </article>
        </div>
        <div
          v-if="deleteTarget !== null"
          class="delete-confirm"
          role="alertdialog"
          aria-labelledby="delete-title"
          aria-describedby="delete-description"
        >
          <h3 id="delete-title">删除这次练习？</h3>
          <p id="delete-description">作文、评阅及题图将永久删除。</p>
          <button
            class="button dark"
            :disabled="deleteBusy"
            @click="deleteRecord"
          >
            {{ deleteBusy ? '正在删除…' : '确认删除' }}</button
          ><button
            class="text-button"
            :disabled="deleteBusy"
            @click="deleteTarget = null"
          >
            保留记录
          </button>
        </div>
        <ReviewResult
          v-if="result && records.some((row) => row.id === result?.id)"
          :result="result"
        />
      </section>

      <section
        v-show="tab === 'knowledge'"
        id="panel-knowledge"
        role="tabpanel"
        aria-labelledby="tab-knowledge"
        class="knowledge-panel"
      >
        <p class="eyebrow">Q&A</p>
        <h2>写作问答</h2>
        <form @submit.prevent="ask">
          <label for="qa-exam">写作类型</label
          ><select id="qa-exam" v-model="exam" :disabled="qaBusy || busy">
            <option v-for="option in EXAMS" :key="option">
              {{ option }}
            </option></select
          ><label for="question">问题</label
          ><textarea
            id="question"
            v-model="question"
            rows="4"
            maxlength="2000"
            required
            :disabled="qaBusy"
            placeholder=""
          ></textarea
          ><button class="button dark" :disabled="qaBusy || !question.trim()">
            {{ qaBusy ? '回答中…' : '提问 ↗' }}
          </button>
        </form>
        <p v-if="qaError" class="error" role="alert">{{ qaError }}</p>
        <article v-if="answer" class="answer-panel" aria-live="polite">
          <h3>回答</h3>
          <p class="pre-wrap">{{ answer }}</p>
        </article>
        <p class="privacy-note">AI 回答</p>
      </section>
    </div>
  </div>
</template>
