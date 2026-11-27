import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ScoreHistory from '../src/components/ScoreHistory.vue'

const observe = vi.fn()
beforeEach(() => {
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe = observe
      unobserve = vi.fn()
      disconnect = vi.fn()
    },
  )
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})
const records = [
  {
    id: 1,
    exam_type: 'GENERAL',
    primary_score: 80,
    primary_max: 100,
    created_at: '2026-11-25T12:00:00Z',
  },
  {
    id: 2,
    exam_type: 'IELTS',
    exam_subtype: 'Task 1',
    primary_score: 6,
    primary_max: 9,
    created_at: '2026-11-26T12:00:00Z',
  },
  {
    id: 3,
    exam_type: 'IELTS',
    exam_subtype: 'Task 2',
    primary_score: 7,
    primary_max: 9,
    created_at: '2026-11-27T12:00:00Z',
  },
  {
    id: 4,
    exam_type: 'GENERAL',
    primary_score: null,
    primary_max: 100,
    created_at: '2026-11-27T12:00:00Z',
  },
]

describe('history trend', () => {
  it('does not mix exams, tasks, or failed scores', async () => {
    const wrapper = mount(ScoreHistory, { props: { records } })
    expect(wrapper.findAll('option')).toHaveLength(3)
    expect(wrapper.findAll('.trend-dot')).toHaveLength(1)
    expect(wrapper.find('tbody').text()).toContain('80 / 100')
    await wrapper.find('select').setValue('IELTS|Task 1|9')
    expect(wrapper.find('tbody').text()).toContain('6 / 9')
    expect(wrapper.find('tbody').text()).not.toContain('7 / 9')
  })
  it('starts observing a chart when async history first arrives', async () => {
    const wrapper = mount(ScoreHistory, { props: { records: [] } })
    expect(wrapper.find('svg').exists()).toBe(false)
    await wrapper.setProps({ records })
    expect(observe).toHaveBeenCalled()
    expect(wrapper.find('svg').exists()).toBe(true)
    wrapper.unmount()
  })
})
