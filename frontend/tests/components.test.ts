import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import HomePage from '../src/components/HomePage.vue'
import ReviewResult from '../src/components/ReviewResult.vue'

describe('HomePage', () => {
  it('uses educational photography and links to the studio', () => {
    const wrapper = mount(HomePage, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    expect(wrapper.find('h1').text()).toContain('更进一步')
    expect(wrapper.find('.hero-image').attributes('src')).toBe(
      '/images/library.jpg',
    )
    expect(wrapper.findAll('.scene-card')).toHaveLength(3)
    expect(wrapper.text()).not.toContain('DeepSeek')
    expect(wrapper.find('.hero-description').text()).toBe(
      '英语写作，细致评阅。',
    )
    expect(wrapper.text()).not.toContain('选择写作类型')
  })
})
describe('ReviewResult', () => {
  it('renders a legitimate zero score, feedback and coaching', () => {
    const wrapper = mount(ReviewResult, {
      props: {
        result: {
          exam_type: '托福（TOEFL）',
          primary_score: 0,
          primary_max: 5,
          score_details: { 任务完成: 0 },
          overall_summary: 'Keep practicing.',
          feedback_dimensions: {
            grammar: {
              strengths: 'Clear',
              improvements: 'Past tense',
              tips: [
                { title: 'Tense', comment: 'Use was', example: 'I was here.' },
              ],
            },
          },
          coach_plan: {
            action_items: [{ title: 'Revise', detail: 'Check verbs.' }],
            model_essay: {
              title: 'Sample',
              text: 'An AI example.',
              highlights: ['Structure'],
            },
          },
        },
      },
    })
    expect(wrapper.find('.score-line strong').text()).toBe('0')
    expect(wrapper.text()).toContain('I was here.')
    expect(wrapper.text()).toContain('Check verbs.')
    expect(wrapper.text()).toContain('An AI example.')
    expect(wrapper.text()).toContain('Past tense')
    expect(wrapper.text()).toContain('Structure')
    expect(wrapper.text()).toContain('非官方范文')
  })
  it('treats untrusted model output as text rather than HTML', () => {
    const wrapper = mount(ReviewResult, {
      props: {
        result: {
          exam_type: 'GENERAL',
          overall_summary: '<img src=x onerror=alert(1)>',
          score_error: 'failed',
        },
      },
    })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('[role="alert"]').text()).toContain('未成功')
    expect(wrapper.find('.score-line').exists()).toBe(false)
  })
})
