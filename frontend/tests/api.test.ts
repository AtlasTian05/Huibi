import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, post } from '../src/api'

afterEach(() => vi.unstubAllGlobals())
describe('API client', () => {
  it('sends same-origin cookies and JSON', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response('{"answer":"ok"}', { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    expect(await post('/questions', { question: 'Hello' })).toEqual({
      answer: 'ok',
    })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/questions',
      expect.objectContaining({
        credentials: 'same-origin',
        method: 'POST',
        body: '{"question":"Hello"}',
      }),
    )
  })
  it('handles empty responses', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    )
    expect(await api('/auth/logout')).toBeUndefined()
  })
  it('shows schema validation details', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            '{"detail":[{"msg":"Value error, 作文需为 20–1000 词"}]}',
            { status: 422 },
          ),
        ),
    )
    await expect(api('/reviews')).rejects.toThrow('作文需为 20–1000 词')
  })
  it('normalizes non-JSON and network failures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('Bad gateway', { status: 502 })),
    )
    await expect(api('/reviews')).rejects.toBeInstanceOf(ApiError)
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('fetch failed')),
    )
    await expect(api('/reviews')).rejects.toThrow('无法连接服务')
  })
})
