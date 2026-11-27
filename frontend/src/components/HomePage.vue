<script setup lang="ts">
const scenes = [
  {
    no: '01',
    title: '通用英语',
    label: 'GENERAL',
    text: '日常练笔 · 观点表达',
    tag: '通用',
  },
  {
    no: '02',
    title: '雅思写作',
    label: 'IELTS',
    text: '图表描述 · 议论文',
    tag: '雅思',
  },
  {
    no: '03',
    title: '托福写作',
    label: 'TOEFL',
    text: '学术讨论 · 邮件写作',
    tag: '托福',
  },
]
</script>

<template>
  <section class="hero" aria-labelledby="hero-title">
    <img
      class="hero-image"
      src="/images/library.jpg"
      alt="阳光下的图书馆长廊，两侧书架延伸向远方"
      fetchpriority="high"
    />
    <div class="hero-shade"></div>
    <div class="hero-copy">
      <p class="eyebrow light">HUIBI / WRITING</p>
      <h1 id="hero-title">让表达，<br />更进一步。</h1>
      <p class="hero-description">英语写作，细致评阅。</p>
      <div class="hero-actions">
        <RouterLink class="button white" to="/studio"
          >开始写作 <span aria-hidden="true">↗</span></RouterLink
        >
        <a class="hero-secondary" href="#possibilities"
          >写作场景 <span aria-hidden="true">↓</span></a
        >
      </div>
    </div>
    <div class="hero-bottom">
      <span>HUIBI</span><span>英语写作 <i aria-hidden="true">↓</i></span
      ><span class="hero-edition">01 / 03</span>
    </div>
  </section>

  <section
    id="possibilities"
    class="scenes section-shell"
    aria-labelledby="scenes-title"
  >
    <div class="section-heading">
      <div>
        <p class="eyebrow">WRITING</p>
        <h2 id="scenes-title">不同目标，同样专注。</h2>
      </div>
    </div>
    <div class="scene-grid">
      <article v-for="scene in scenes" :key="scene.no" class="scene-card">
        <div class="scene-card-top">
          <span>{{ scene.no }}</span
          ><span>{{ scene.tag }}</span>
        </div>
        <p class="eyebrow">{{ scene.label }}</p>
        <h3>{{ scene.title }}</h3>
        <p>{{ scene.text }}</p>
        <RouterLink to="/studio" :aria-label="`开始${scene.title}写作`"
          >开始写作 <span aria-hidden="true">↗</span></RouterLink
        >
      </article>
    </div>
  </section>

  <section class="feature-banner" aria-labelledby="vision-title">
    <img
      src="/images/writing.jpg"
      alt="学习者在桌前翻阅资料并书写笔记"
      loading="lazy"
    />
    <div class="feature-overlay"></div>
    <div class="feature-copy">
      <p class="eyebrow light">TEXT & IMAGE</p>
      <h2 id="vision-title">图文之间，<br />理解更完整。</h2>
      <p>雅思 Task 1 图文评阅。</p>
      <RouterLink class="button white" to="/studio"
        >图文批改 <span aria-hidden="true">↗</span></RouterLink
      >
    </div>
    <a
      class="photo-credit"
      href="https://unsplash.com/photos/sXZ8vvFrTCI"
      target="_blank"
      rel="noreferrer"
      >摄影：Alexa Williams / Unsplash ↗</a
    >
  </section>

  <section
    id="approach"
    class="approach section-shell"
    aria-labelledby="approach-title"
  >
    <div class="section-heading">
      <div>
        <p class="eyebrow">REVIEW</p>
        <h2 id="approach-title">不止于分数。</h2>
      </div>
      <RouterLink class="underlined-link" to="/studio"
        >进入工作台 ↗</RouterLink
      >
    </div>
    <div class="steps">
      <article>
        <span>01 / FEEDBACK</span>
        <h3>细致评阅</h3>
        <p>量表评分 · 四维解析</p>
      </article>
      <article>
        <span>02 / REVISION</span>
        <h3>针对性修改</h3>
        <p>修改建议 · 表达示例</p>
      </article>
      <article>
        <span>03 / PRACTICE</span>
        <h3>持续练习</h3>
        <p>专项练习 · 写作档案</p>
      </article>
    </div>
  </section>
</template>
