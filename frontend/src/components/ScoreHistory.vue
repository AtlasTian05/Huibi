<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Submission } from '../types'
const props = defineProps<{ records: Submission[] }>()
const selected = ref('')
const hovered = ref<number | null>(null)
const width = ref(640)
const host = ref<HTMLElement | null>(null)
let observer: ResizeObserver | undefined
const groupKey = (row: Submission) =>
  `${row.exam_type}|${row.exam_subtype || ''}|${row.primary_max}`
const groups = computed(() => {
  const map = new Map<string, string>()
  for (const row of props.records) {
    if (
      row.primary_score == null ||
      !row.primary_max ||
      !Number.isFinite(row.primary_score)
    )
      continue
    map.set(
      groupKey(row),
      `${row.exam_subtype || row.exam_type} · 满分 ${row.primary_max}`,
    )
  }
  return [...map].map(([value, label]) => ({ value, label }))
})
watch(
  groups,
  (list) => {
    if (!list.some((item) => item.value === selected.value))
      selected.value = list[0]?.value || ''
  },
  { immediate: true },
)
watch(selected, () => {
  hovered.value = null
})
const rows = computed(() =>
  props.records
    .filter(
      (row) =>
        groupKey(row) === selected.value &&
        row.primary_score != null &&
        Number.isFinite(row.primary_score) &&
        Number.isFinite(new Date(row.created_at || '').getTime()),
    )
    .sort(
      (a, b) =>
        new Date(a.created_at!).getTime() - new Date(b.created_at!).getTime(),
    ),
)
const max = computed(() => rows.value[0]?.primary_max || 100)
const points = computed(() =>
  rows.value.map((row, index) => {
    const first = new Date(rows.value[0].created_at!).getTime()
    const last = new Date(rows.value.at(-1)!.created_at!).getTime()
    const fraction =
      last === first
        ? rows.value.length === 1
          ? 0.5
          : index / (rows.value.length - 1)
        : (new Date(row.created_at!).getTime() - first) / (last - first)
    return {
      row,
      x: 42 + fraction * (width.value - 65),
      y: 180 - (row.primary_score! / max.value) * 150,
    }
  }),
)
const path = computed(() =>
  points.value.map((point) => `${point.x},${point.y}`).join(' '),
)
const active = computed(() =>
  hovered.value == null ? null : points.value[hovered.value],
)
const date = (value: string) =>
  new Date(value).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  })
function move(event: PointerEvent) {
  const bounds = (event.currentTarget as SVGElement).getBoundingClientRect()
  const x = ((event.clientX - bounds.left) * width.value) / bounds.width
  let closest = 0
  points.value.forEach((point, index) => {
    if (Math.abs(point.x - x) < Math.abs(points.value[closest].x - x))
      closest = index
  })
  hovered.value = points.value.length ? closest : null
}
onMounted(() => {
  observer = new ResizeObserver((entries) => {
    if (entries[0].contentRect.width > 0)
      width.value = Math.max(250, entries[0].contentRect.width)
  })
  if (host.value) observer.observe(host.value)
})
watch(host, (element, oldElement) => {
  if (oldElement) observer?.unobserve(oldElement)
  if (element) observer?.observe(element)
})
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <section
    v-if="groups.length"
    class="history-trend"
    aria-labelledby="trend-title"
  >
    <div class="trend-filters">
      <label for="trend-type">任务与量表</label
      ><select id="trend-type" v-model="selected">
        <option v-for="group in groups" :key="group.value" :value="group.value">
          {{ group.label }}
        </option>
      </select>
    </div>
    <div ref="host" class="trend-frame">
      <h3 id="trend-title">得分趋势</h3>
      <p class="muted small">AI 模拟评分 · 非官方成绩</p>
      <svg
        v-if="points.length"
        :viewBox="`0 0 ${width} 220`"
        class="trend-svg"
        role="img"
        aria-label="当前任务类型的历史得分折线图，下方可展开完整数据表"
        @pointermove="move"
        @pointerleave="hovered = null"
      >
        <g v-for="tick in [0, max / 2, max]" :key="tick">
          <line
            x1="42"
            :x2="width - 23"
            :y1="180 - (tick / max) * 150"
            :y2="180 - (tick / max) * 150"
            class="trend-grid"
          />
          <text x="30" :y="184 - (tick / max) * 150" text-anchor="end">
            {{ tick }}
          </text>
        </g>
        <polyline v-if="points.length > 1" :points="path" class="trend-line" />
        <line
          v-if="active"
          :x1="active.x"
          :x2="active.x"
          y1="20"
          y2="180"
          class="trend-crosshair"
        />
        <g v-for="(point, index) in points" :key="point.row.id || index">
          <circle :cx="point.x" :cy="point.y" r="4" class="trend-dot" />
          <circle
            :cx="point.x"
            :cy="point.y"
            r="12"
            fill="transparent"
            tabindex="0"
            :aria-label="`${date(point.row.created_at!)}，${point.row.primary_score} 分`"
            @focus="hovered = index"
            @blur="hovered = null"
          />
        </g>
        <text v-if="points[0]" x="42" y="208">
          {{ date(points[0].row.created_at!) }}
        </text>
        <text
          v-if="points.length > 1"
          :x="width - 23"
          y="208"
          text-anchor="end"
        >
          {{ date(points.at(-1)!.row.created_at!) }}
        </text>
      </svg>
      <div class="trend-readout" aria-live="polite">
        <template v-if="active"
          ><strong>{{ active.row.primary_score }} / {{ max }}</strong
          ><span
            >{{ new Date(active.row.created_at!).toLocaleString('zh-CN') }} ·
            {{ active.row.essay_topic || '未命名练习' }}</span
          ></template
        ><span v-else>{{ rows.length }} 次练习</span>
      </div>
      <details>
        <summary>数据表（{{ rows.length }} 次）</summary>
        <table class="rubric-table">
          <thead>
            <tr>
              <th scope="col">日期</th>
              <th scope="col">得分 / 满分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="row.id || index">
              <th scope="row">
                {{ new Date(row.created_at!).toLocaleString('zh-CN') }}
              </th>
              <td>{{ row.primary_score }} / {{ row.primary_max }}</td>
            </tr>
          </tbody>
        </table>
      </details>
    </div>
  </section>
</template>

<style scoped>
.history-trend {
  margin: 24px 0 32px;
  --viz-surface: #fff;
  --viz-ink: #191919;
  --viz-muted: #666;
  --viz-grid: #e7e7e7;
  --viz-line: #257de0;
  color: var(--viz-ink);
  color-scheme: light;
}
.trend-filters {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.trend-filters label {
  font-size: 11px;
  margin: 0;
}
.trend-filters select {
  width: auto;
  max-width: 100%;
  font-size: 11px;
}
.trend-frame {
  background: var(--viz-surface);
  border: 1px solid var(--line);
  padding: 22px;
  min-width: 0;
}
.trend-frame h3 {
  font-size: 17px;
  font-weight: 500;
  margin-bottom: 6px;
}
.trend-svg {
  display: block;
  width: 100%;
  margin-top: 18px;
  touch-action: pan-y;
  overflow: visible;
}
.trend-svg text {
  fill: var(--viz-muted);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}
.trend-grid {
  stroke: var(--viz-grid);
  stroke-width: 1;
}
.trend-line {
  fill: none;
  stroke: var(--viz-line);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.trend-dot {
  fill: var(--viz-line);
  stroke: var(--viz-surface);
  stroke-width: 2;
}
.trend-crosshair {
  stroke: var(--viz-muted);
  stroke-width: 1;
  opacity: 0.5;
}
.trend-readout {
  min-height: 44px;
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 11px;
}
.trend-readout > span {
  color: var(--viz-muted);
}
.trend-readout > strong {
  font-size: 15px;
  white-space: nowrap;
  font-weight: 500;
}
.trend-frame details {
  font-size: 11px;
  margin-top: 12px;
}
.trend-frame summary {
  cursor: pointer;
}
.trend-frame table th {
  padding-left: 0;
}
.trend-frame .rubric-table {
  margin-bottom: 0;
}
.trend-svg circle:focus {
  outline: none;
  stroke: var(--viz-ink);
  stroke-width: 1;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) .history-trend {
    --viz-surface: #191919;
    --viz-ink: #efefef;
    --viz-muted: #9c9c9c;
    --viz-grid: #303030;
    --viz-line: #338ced;
    color-scheme: dark;
  }
}
:root[data-theme='dark'] .history-trend {
  --viz-surface: #191919;
  --viz-ink: #efefef;
  --viz-muted: #9c9c9c;
  --viz-grid: #303030;
  --viz-line: #338ced;
  color-scheme: dark;
}
@media (forced-colors: active) {
  .trend-line {
    stroke: CanvasText;
  }
  .trend-dot {
    fill: CanvasText;
  }
  .trend-grid {
    stroke: GrayText;
  }
}
@media (max-width: 760px) {
  .trend-frame {
    padding: 16px;
  }
  .trend-readout {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
    min-height: 60px;
  }
}
</style>
