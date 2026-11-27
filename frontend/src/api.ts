export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      ...options,
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
  } catch {
    throw new ApiError('无法连接服务，请检查后端是否启动。', 0)
  }
  if (!response.ok) {
    let message = '请求失败，请稍后重试。'
    try {
      const body = await response.json()
      message = Array.isArray(body.detail)
        ? body.detail
            .map((item: { msg: string }) =>
              item.msg.replace('Value error, ', ''),
            )
            .join('；')
        : body.detail || message
    } catch {
      /* Non-JSON proxy errors use the safe message above. */
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function post<T>(path: string, body: unknown) {
  return api<T>(path, { method: 'POST', body: JSON.stringify(body) })
}
