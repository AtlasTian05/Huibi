import { test, expect, type Page } from '@playwright/test'
const essay =
  'Learning a language requires patience and regular practice. Writing allows students to organize their ideas clearly and develop confidence through thoughtful feedback and revision.'
const result = {
  id: 1,
  exam_type: '雅思（IELTS）',
  primary_score: 6.5,
  primary_max: 9,
  essay_topic: 'A practice essay',
  created_at: '2026-11-27T08:00:00Z',
  essay_text: essay,
  score_details: { 内容与任务完成: 6.5 },
  overall_summary: '论点清楚，可进一步丰富例证。',
  feedback_dimensions: {
    content: {
      strengths: '观点明确',
      improvements: '补充例证',
      tips: [
        {
          title: '加入细节',
          comment: '用具体事例支持论点',
          example: 'For example, daily writing builds confidence.',
        },
      ],
    },
  },
  coach_plan: {
    action_items: [{ title: '补充例子', detail: '为主体段加入一个具体例子。' }],
  },
}
async function mockApi(page: Page, authenticated = true) {
  await page.route('**/api/auth/me', (route) =>
    route.fulfill({
      status: authenticated ? 200 : 401,
      json: authenticated ? { username: 'learner' } : { detail: '请先登录' },
    }),
  )
  await page.route('**/api/auth/login', (route) =>
    route.fulfill({ json: { username: 'learner' } }),
  )
  await page.route('**/api/auth/register', (route) =>
    route.fulfill({ status: 201, json: { message: '注册成功' } }),
  )
  await page.route('**/api/submissions', (route) => route.fulfill({ json: [] }))
}

test.afterEach(async ({ page }) => {
  if (page.url() === 'about:blank') return
  await expect(page.locator('body')).toHaveJSProperty(
    'scrollWidth',
    await page.evaluate(() => window.innerWidth),
  )
})

test('homepage shows education photos without horizontal overflow', async ({
  page,
}, testInfo) => {
  await mockApi(page, false)
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toContainText('让表达')
  await expect(page.locator('.hero-image')).toHaveJSProperty(
    'naturalWidth',
    2400,
  )
  await expect(page.locator('body')).toHaveJSProperty(
    'scrollWidth',
    await page.evaluate(() => window.innerWidth),
  )
  await page.screenshot({
    path: `test-results/home-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page
    .locator('.hero-actions')
    .getByRole('link', { name: '开始写作' })
    .click()
  await expect(page).toHaveURL('/login')
})

test('registration then login opens the real Vue studio', async ({
  page,
}, testInfo) => {
  await mockApi(page, false)
  await page.goto('/login')
  await page.screenshot({
    path: `test-results/login-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: '注册', exact: true }),
  ).toBeVisible()
  await page.screenshot({
    path: `test-results/register-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.getByLabel('用户名').fill('learner')
  await page.getByLabel('密码', { exact: true }).fill('example-password')
  await page.getByRole('button', { name: '创建账号 ↗' }).click()
  await expect(page.getByRole('status')).toContainText('注册成功')
  await page.getByLabel('密码', { exact: true }).fill('example-password')
  await page.getByRole('button', { name: '登录工作台' }).click()
  await expect(page).toHaveURL('/studio')
  await expect(page.getByRole('button', { name: '开始评阅' })).toBeDisabled()
})

test('Task 1 upload, review, feedback, and archive deletion', async ({
  page,
}, testInfo) => {
  await mockApi(page)
  let captured: Record<string, string> = {}
  await page.route('**/api/reviews', async (route) => {
    captured = route.request().postDataJSON()
    await route.fulfill({ status: 201, json: result })
  })
  await page.goto('/studio')
  await page
    .locator('#panel-write')
    .getByLabel('写作类型', { exact: true })
    .selectOption('雅思（IELTS）')
  await page
    .getByLabel('任务类型', { exact: true })
    .selectOption('IELTS Writing Task 1（图表/图片描述）')
  await page.getByLabel('Task 1 题图').setInputFiles({
    name: 'chart.png',
    mimeType: 'image/png',
    buffer: Buffer.from(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aZioAAAAASUVORK5CYII=',
      'base64',
    ),
  })
  await page.getByLabel('英文作文').fill(essay)
  await page.screenshot({
    path: `test-results/studio-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.getByRole('button', { name: '开始评阅' }).click()
  await expect(
    page.getByRole('heading', { name: '评阅结果' }).first(),
  ).toBeVisible()
  expect(captured.essay_image_mime).toBe('image/png')
  expect(captured.essay_image_b64).toBeTruthy()
  await expect(page.locator('.score-line').first()).toContainText('6.5')
  await expect(page.getByText('用具体事例支持论点')).toBeVisible()
  await expect(page.getByText('为主体段加入一个具体例子。')).toBeVisible()
  await page.screenshot({
    path: `test-results/result-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await expect(page.locator('body')).toHaveJSProperty(
    'scrollWidth',
    await page.evaluate(() => window.innerWidth),
  )
  await page.route('**/api/submissions', (route) =>
    route.fulfill({ json: [result] }),
  )
  await page.getByRole('tab', { name: '档案' }).click()
  await expect(page.locator('.history-row')).toHaveCount(1)
  await page.route('**/api/submissions/1', (route) =>
    route.fulfill({ status: 204 }),
  )
  await page.getByRole('button', { name: '删除', exact: true }).click()
  await page.getByRole('button', { name: '确认删除' }).click()
  await expect(page.locator('.history-row')).toHaveCount(0)
})

test('changing task removes stale uploaded images', async ({ page }) => {
  await mockApi(page)
  await page.goto('/studio')
  await page
    .locator('#panel-write')
    .getByLabel('写作类型', { exact: true })
    .selectOption('雅思（IELTS）')
  await page
    .getByLabel('任务类型', { exact: true })
    .selectOption('IELTS Writing Task 1（图表/图片描述）')
  await page.getByLabel('Task 1 题图').setInputFiles({
    name: 'chart.png',
    mimeType: 'image/png',
    buffer: Buffer.from('image'),
  })
  await expect(page.getByRole('button', { name: '移除图片' })).toBeVisible()
  await page
    .getByLabel('任务类型', { exact: true })
    .selectOption('IELTS Writing Task 2（议论文）')
  await expect(page.locator('.image-preview')).toHaveCount(0)
  await expect(page.getByLabel('Task 1 题图')).toHaveCount(0)
})

test('service errors preserve the essay for retry', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/reviews', (route) =>
    route.fulfill({ status: 502, json: { detail: '模型服务暂不可用' } }),
  )
  await page.goto('/studio')
  await page.getByLabel('英文作文').fill(essay)
  await page.getByRole('button', { name: '开始评阅' }).click()
  await expect(page.getByRole('alert')).toContainText('模型服务暂不可用')
  await expect(page.getByLabel('英文作文')).toHaveValue(essay)
  await expect(page.getByRole('button', { name: '开始评阅' })).toBeEnabled()
})

test('knowledge questions display the API answer as safe text', async ({
  page,
}, testInfo) => {
  await mockApi(page)
  await page.route('**/api/questions', (route) =>
    route.fulfill({
      json: { answer: '用清晰的主题句组织段落。<script>alert(1)</script>' },
    }),
  )
  await page.goto('/studio')
  await page.getByRole('tab', { name: '问答' }).click()
  await page.getByLabel('问题').fill('如何组织段落？')
  await page.getByRole('button', { name: '提问' }).click()
  await expect(page.locator('.answer-panel')).toContainText('用清晰的主题句')
  await expect(page.locator('.answer-panel script')).toHaveCount(0)
  await page.screenshot({
    path: `test-results/qa-${testInfo.project.name}.png`,
    fullPage: true,
  })
})

test('FastAPI health endpoint works without an API key', async ({
  request,
}) => {
  const response = await request.get('/api/health')
  expect(response.ok()).toBeTruthy()
  expect((await response.json()).version).toBe('2.0.0')
})

test('history trend filters incompatible scales and exposes its data table', async ({
  page,
}, testInfo) => {
  await mockApi(page)
  const history = [
    {
      ...result,
      id: 3,
      primary_score: 7.5,
      created_at: '2026-11-27T08:00:00Z',
    },
    { ...result, id: 2, primary_score: 7, created_at: '2026-11-25T08:00:00Z' },
    {
      ...result,
      id: 1,
      primary_score: 6.5,
      created_at: '2026-11-20T08:00:00Z',
    },
    {
      ...result,
      id: 4,
      exam_type: '通用英语作文评测',
      primary_score: 80,
      primary_max: 100,
    },
  ]
  await page.route('**/api/submissions', (route) =>
    route.fulfill({ json: history }),
  )
  await page.goto('/studio')
  await page.getByRole('tab', { name: '档案' }).click()
  await expect(page.locator('.trend-dot')).toHaveCount(3)
  await page.locator('.trend-frame summary').click()
  await expect(page.locator('.trend-frame tbody tr')).toHaveCount(3)
  await page.screenshot({
    path: `test-results/trend-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.getByLabel('任务与量表').selectOption('通用英语作文评测||100')
  await expect(page.locator('.trend-dot')).toHaveCount(1)
  await expect(page.locator('.trend-frame tbody')).toContainText('80 / 100')
  await expect(page.locator('body')).toHaveJSProperty(
    'scrollWidth',
    await page.evaluate(() => window.innerWidth),
  )
})

test('empty archive stays concise and opens writing', async ({
  page,
}, testInfo) => {
  await mockApi(page)
  await page.goto('/studio')
  await page.getByRole('tab', { name: '档案' }).click()
  await expect(page.getByRole('heading', { name: '暂无记录' })).toBeVisible()
  await expect(page.locator('.empty-state p')).toHaveCount(0)
  await page.screenshot({
    path: `test-results/empty-${testInfo.project.name}.png`,
    fullPage: true,
  })
  await page.getByRole('button', { name: '开始写作' }).click()
  await expect(page.getByLabel('英文作文')).toBeVisible()
})

test('pending review uses a brief state and keeps the full returned feedback', async ({
  page,
}, testInfo) => {
  await mockApi(page)
  let release!: () => void
  const gate = new Promise<void>((resolve) => {
    release = resolve
  })
  await page.route('**/api/reviews', async (route) => {
    await gate
    await route.fulfill({ status: 201, json: result })
  })
  await page.goto('/studio')
  await page.getByLabel('英文作文').fill(essay)
  await page.getByRole('button', { name: '开始评阅' }).click()
  try {
    await expect(page.locator('.processing')).toHaveText('评阅中…')
    await expect(page.getByLabel('英文作文')).toBeDisabled()
    await page.screenshot({
      path: `test-results/pending-${testInfo.project.name}.png`,
      fullPage: true,
    })
  } finally {
    release()
  }
  await expect(
    page.getByRole('heading', { name: '评阅结果' }).first(),
  ).toBeVisible()
  await expect(
    page.getByText('For example, daily writing builds confidence.'),
  ).toBeVisible()
})
