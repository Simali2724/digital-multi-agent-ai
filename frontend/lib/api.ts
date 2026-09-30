export type Provider =
  | "auto"
  | "claude"
  | "chatgpt"
  | "gemini"
  | "ollama"

export type HistoryItem = {
  role: "user" | "assistant"
  content: string
}

export type Citation = {
  label: string
  source: string
  page?: number | null
  type: string
}

export type ImagePayload = {
  name: string
  mime_type: string
  data_url: string
}

export type ChatRequest = {
  message: string
  provider: Provider
  history: HistoryItem[]
  image?: ImagePayload
  ingest_image_to_rag?: boolean
}

export type StreamHandlers = {
  onAgent?: (agent: string) => void
  onProvider?: (provider: string) => void
  onToken?: (token: string) => void
  onSources?: (sources: Citation[]) => void
  onError?: (message: string) => void
  onDone?: () => void
}
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000"


function handleSseFrame(
  frame: string,
  handlers: StreamHandlers,
) {
  const lines = frame.split("\n")

  let eventName = "message"

  const dataLines: string[] = []

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line
        .slice(6)
        .trim()
    }

    if (line.startsWith("data:")) {
      dataLines.push(
        line
          .slice(5)
          .trimStart(),
      )
    }
  }

  if (dataLines.length === 0) {
    return
  }

  const rawData =
    dataLines.join("\n")

  let payload: unknown

  try {
    payload = JSON.parse(
      rawData,
    )
  } catch {
    return
  }

  if (
  eventName === "meta" &&
  typeof payload === "object" &&
  payload !== null
) {
  if ("agent" in payload) {
    handlers.onAgent?.(
      String(
        (
          payload as {
            agent: unknown
          }
        ).agent,
      ),
    )
  }

  if ("provider" in payload) {
    handlers.onProvider?.(
      String(
        (
          payload as {
            provider: unknown
          }
        ).provider,
      ),
    )
  }

  return
}

  if (
    eventName === "token" &&
    typeof payload === "object" &&
    payload !== null &&
    "text" in payload
  ) {
    handlers.onToken?.(
      String(
        (
          payload as {
            text: unknown
          }
        ).text,
      ),
    )

    return
  }

  if (
    eventName === "sources" &&
    Array.isArray(payload)
  ) {
    handlers.onSources?.(
      payload as Citation[],
    )

    return
  }

  if (
    eventName === "error" &&
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload
  ) {
    handlers.onError?.(
      String(
        (
          payload as {
            message: unknown
          }
        ).message,
      ),
    )

    return
  }

  if (eventName === "done") {
    handlers.onDone?.()
  }
}


export async function streamChat(
  request: ChatRequest,
  handlers: StreamHandlers,
  signal?: AbortSignal,
) {
  const response = await fetch(
    `${API_BASE_URL}/chat/stream`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify(
        request,
      ),

      signal,
    },
  )

  if (
    !response.ok ||
    !response.body
  ) {
    throw new Error(`Unable to send the request (HTTP ${response.status}). Please try again.`)
  }

  const reader =
    response.body.getReader()

  const decoder =
    new TextDecoder()

  let buffer = ""

  while (true) {
    const {
      done,
      value,
    } = await reader.read()

    if (done) {
      break
    }

    buffer += decoder
      .decode(
        value,
        {
          stream: true,
        },
      )
      .replace(
        /\r\n/g,
        "\n",
      )

    let boundary =
      buffer.indexOf(
        "\n\n",
      )

    while (
      boundary !== -1
    ) {
      const frame = buffer
        .slice(
          0,
          boundary,
        )
        .trim()

      buffer = buffer.slice(
        boundary + 2,
      )

      if (frame) {
        handleSseFrame(
          frame,
          handlers,
        )
      }

      boundary =
        buffer.indexOf(
          "\n\n",
        )
    }
  }

  const remaining =
    buffer.trim()

  if (remaining) {
    handleSseFrame(
      remaining,
      handlers,
    )
  }
}


export async function fileToImagePayload(
  file: File,
): Promise<ImagePayload> {
  const dataUrl =
    await new Promise<string>(
      (
        resolve,
        reject,
      ) => {
        const reader =
          new FileReader()

        reader.onload = () => {
          resolve(
            String(
              reader.result,
            ),
          )
        }

        reader.onerror = () => {
          reject(
            reader.error ??
              new Error(
                "Unable to read image.",
              ),
          )
        }

        reader.readAsDataURL(
          file,
        )
      },
    )

  return {
    name: file.name,

    mime_type:
      file.type ||
      "application/octet-stream",

    data_url: dataUrl,
  }
}
export async function fetchProducts(): Promise<{id: string; name: string; price: string; warranty: string}[]> {
  const response = await fetch(`${API_BASE_URL}/products`)
  if (!response.ok) throw new Error("Catalog unavailable")
  const products: {id: string; name: string; price: string; warranty_months: number}[] = await response.json()
  return products.map((p) => ({ id: p.id, name: p.name, price: p.price, warranty: `${p.warranty_months} month demo warranty` }))
}
