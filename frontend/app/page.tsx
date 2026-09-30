"use client"

import ReactMarkdown from "react-markdown"

import {
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react"

import {
  Bot,
  BookOpen,
  Eye,
  ImageIcon,
  LoaderCircle,
  Paperclip,
  Send,
  ShoppingBag,
  Sparkles,
  Wrench,
  X,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import { ScrollArea } from "@/components/ui/scroll-area"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"

import {
  fetchProducts,
  fileToImagePayload,
  ImagePayload,
  Provider,
  streamChat,
} from "@/lib/api"


// ============================================================
// Local UI message
// ============================================================

type Message = {
  id: string

  role:
    | "user"
    | "assistant"

  content: string

  agent?: string

  requestedProvider?: Provider

  actualProvider?: string

  imagePreview?: string

  imageName?: string
}


// ============================================================
// Exact hackathon product data
// ============================================================




// ============================================================
// Model selector
// ============================================================

const MODELS: {
  provider: Provider
  label: string
  model: string
}[] = [
  {
    provider: "auto",
    label: "Auto (Recommended)",
    model: "Chooses best available model",
  },
  {
    provider: "claude",
    label: "Claude",
    model: "Anthropic",
  },
  {
    provider: "chatgpt",
    label: "ChatGPT",
    model: "OpenAI",
  },
  {
    provider: "gemini",
    label: "Gemini",
    model: "Google AI",
  },
  {
    provider: "ollama",
    label: "Ollama",
    model: "Local model",
  },
]


const PROVIDER_LABELS: Record<string, string> = {
  auto: "Auto",
  claude: "Claude",
  chatgpt: "ChatGPT",
  gemini: "Gemini",
  ollama: "Ollama",
}


// ============================================================
// Suggested prompts
// ============================================================

const SUGGESTED_PROMPTS = [
  "What is the price and warranty of P001?",

  "What is the status of service ticket SR-1001?",

  "Track order ORD-9001.",

  "According to the knowledge base, what is the warranty of the Daikin AC P002?",
]


// ============================================================
// Agent information
// ============================================================

const AGENTS: Record<
  string,
  {
    label: string
    icon: typeof Bot
  }
> = {
  sales_agent: {
    label: "Sales Agent",
    icon: ShoppingBag,
  },

  resq_agent: {
    label: "resQ Agent",
    icon: Wrench,
  },

  rag_agent: {
    label: "Knowledge Support",
    icon: BookOpen,
  },

  vision_agent: {
    label: "Vision Agent",
    icon: Eye,
  },
}


// ============================================================
// Agent badge
// ============================================================

function AgentBadge({
  agent,
}: {
  agent?: string
}) {
  if (!agent) {
    return null
  }

  const config =
    AGENTS[agent] ?? {
      label: agent,
      icon: Bot,
    }

  const Icon =
    config.icon

  return (
    <Badge
      variant="secondary"
      className="
        gap-1.5
        rounded-full
        px-2.5
        py-1
      "
    >
      <Icon
        className="size-3.5"
      />

      {config.label}
    </Badge>
  )
}


// ============================================================
// Main page
// ============================================================

export default function Home() {
  const [products, setProducts] = useState<{ id: string; name: string; price: string; warranty: string }[]>([])
  useEffect(() => {
    let active = true
    fetchProducts().then((items) => { if (active) setProducts(items) }).catch(() => {})
    return () => { active = false }
  }, [])

  const [
    messages,
    setMessages,
  ] = useState<Message[]>([])

  const [
    input,
    setInput,
  ] = useState("")

  const [
    provider,
    setProvider,
  ] = useState<Provider>(
    "auto",
  )

  const [
    image,
    setImage,
  ] = useState<
    ImagePayload | null
  >(null)

  const [
    ingestImage,
    setIngestImage,
  ] = useState(false)

  const [
    isStreaming,
    setIsStreaming,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)

  const fileInputRef =
    useRef<HTMLInputElement>(
      null,
    )

  const endRef =
    useRef<HTMLDivElement>(
      null,
    )


  // ==========================================================
  // Currently selected model
  // ==========================================================

  const selectedModel =
    useMemo(
      () =>
        MODELS.find(
          (item) =>
            item.provider
            === provider,
        ) ?? MODELS[0],

      [provider],
    )


  // ==========================================================
  // Auto-scroll to latest message
  // ==========================================================

  useEffect(
    () => {
      endRef.current
        ?.scrollIntoView({
          behavior: "smooth",
          block: "end",
        })
    },
    [
      messages,
      isStreaming,
    ],
  )


  // ==========================================================
  // Image handling
  // ==========================================================

  async function handleImage(
    file?: File,
  ) {
    if (!file) {
      return
    }

    setError(null)

    if (
      !["image/png", "image/jpeg", "image/webp"].includes(file.type)
    ) {
      setError(
        "Please select a PNG, JPEG or WebP image.",
      )

      return
    }

    const maxSize =
      10 * 1024 * 1024

    if (
      file.size > maxSize
    ) {
      setError(
        "Image must be 10 MB or smaller.",
      )

      return
    }

    try {
      const payload =
        await fileToImagePayload(
          file,
        )

      setImage(payload)

    } catch (imageError) {
      setError(
        imageError
          instanceof Error
          ? imageError.message
          : "Unable to read the image.",
      )
    }
  }


  // ==========================================================
  // Submit chat
  // ==========================================================

  async function handleSubmit(
    event?: FormEvent,
  ) {
    event
      ?.preventDefault()

    if (isStreaming) {
      return
    }

    const messageText =
      input.trim() ||
      (
        image
          ? "Please analyze this image."
          : ""
      )

    if (!messageText) {
      return
    }

    setError(null)
    setIsStreaming(true)

    // Only send previous conversation messages.
    const currentHistory =
      messages.slice(-12)
        .filter(
          (message) =>
            Boolean(
              message
                .content
                .trim(),
            ),
        )
        .map(
          (message) => ({
            role:
              message.role,

            content:
              message.content,
          }),
        )

    const userMessageId =
      crypto.randomUUID()

    const assistantMessageId =
      crypto.randomUUID()

    const attachedImage =
      image

    // Add user + empty assistant message immediately.
    setMessages(
      (previous) => [
        ...previous,

        {
          id:
            userMessageId,

          role:
            "user",

          content:
            messageText,

          imagePreview:
            attachedImage
              ?.data_url,

          imageName:
            attachedImage
              ?.name,
        },

        {
          id:
            assistantMessageId,

          role:
            "assistant",

          content: "",

          requestedProvider: provider,
        },
      ],
    )

    setInput("")
    setImage(null)

    try {
      await streamChat(
        {
          message:
            messageText,

          provider,

          history:
            currentHistory,

          image:
            attachedImage
              ?? undefined,

          ingest_image_to_rag:
            Boolean(
              attachedImage
              &&
              ingestImage,
            ),
        },

        {
          // -----------------------------------------------
          // Agent selected by LangGraph
          // -----------------------------------------------

          onAgent:
            (agent) => {
              setMessages(
                (previous) =>
                  previous.map(
                    (message) =>
                      message.id
                      === assistantMessageId
                        ? {
                            ...message,
                            agent,
                          }
                        : message,
                  ),
              )
            },

          // -----------------------------------------------
          // Live SSE token
          // -----------------------------------------------

          onProvider:
            (actualProvider) => {
              setMessages(
                (previous) =>
                  previous.map(
                    (message) =>
                      message.id
                      === assistantMessageId
                        ? {
                            ...message,
                            actualProvider,
                          }
                        : message,
                  ),
              )
            },


          onToken:
            (token) => {
              setMessages(
                (previous) =>
                  previous.map(
                    (message) =>
                      message.id
                      === assistantMessageId
                        ? {
                            ...message,

                            content:
                              message.content
                              + token,
                          }
                        : message,
                  ),
              )
            },

          // -----------------------------------------------
          // Sources intentionally hidden from UI.
          //
          // Backend can still use RAG internally.
          // -----------------------------------------------

          onSources:
            () => {
              // Intentionally ignored.
            },

          // -----------------------------------------------
          // Backend error
          // -----------------------------------------------

          onError:
            (
              backendError,
            ) => {
              setError(backendError)
              setMessages((previous) => previous.map((message) => message.id === assistantMessageId ? { ...message, content: "Sorry, this request could not be completed. Please try again." } : message))
            },
        },
      )

    } catch (streamError) {
      const errorMessage =
        streamError
          instanceof Error
          ? streamError.message
          : "Unable to contact the backend."

      setError(
        errorMessage,
      )

      setMessages(
        (previous) =>
          previous.map(
            (message) =>
              (
                message.id
                === assistantMessageId
                &&
                !message.content
              )
                ? {
                    ...message,

                    content:
                      (
                        "Request failed: "
                        + errorMessage
                      ),
                  }
                : message,
          ),
      )

    } finally {
      setIsStreaming(
        false,
      )
    }
  }


  // ==========================================================
  // UI
  // ==========================================================

  return (
    <main
      className="
        min-h-screen
        p-3
        md:p-5
      "
    >
      <div
        className="
          mx-auto
          grid
          min-h-[calc(100vh-2rem)]
          max-w-[1600px]
          grid-cols-1
          gap-4
          xl:grid-cols-[minmax(0,1fr)_330px]
        "
      >
        {/* ==================================================
            MAIN CHAT CARD
        ================================================== */}

        <Card
          className="
            flex
            min-h-[90vh]
            min-w-0
            flex-col
            overflow-hidden
            border-black/5
            bg-white/90
            shadow-xl
            backdrop-blur
          "
        >
          {/* ================================================
              HEADER
          ================================================ */}

          <CardHeader
            className="
              border-b
              bg-white/80
              px-4
              py-4
              md:px-6
            "
          >
            <div
              className="
                flex
                flex-col
                gap-4
                sm:flex-row
                sm:items-center
                sm:justify-between
              "
            >
              <div
                className="
                  flex
                  items-center
                  gap-3
                "
              >
                <div
                  className="
                    grid
                    size-12
                    shrink-0
                    place-items-center
                    rounded-full
                    bg-primary
                    text-primary-foreground
                    shadow-sm
                  "
                >
                  <Sparkles
                    className="size-5"
                  />
                </div>

                <div>
                  <CardTitle
                    className="
                      text-xl
                      font-semibold
                    "
                  >
                    Reliance Digital
                    AI Assistant
                  </CardTitle>

                  <p
                    className="
                      mt-1
                      text-sm
                      text-muted-foreground
                    "
                  >
                    Sales + resQ
                    multi-agent
                    support
                  </p>
                </div>
              </div>


              {/* ============================================
                  MODEL SELECTOR
              ============================================ */}

              <Select
                value={provider}

                onValueChange={
                  (value) => {
                    setProvider(
                      value as Provider,
                    )
                  }
                }
              >
                <SelectTrigger
                  className="
                    w-full
                    sm:w-[280px]
                  "
                >
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  {
                    MODELS.map(
                      (model) => (
                        <SelectItem
                          key={
                            model.provider
                          }

                          value={
                            model.provider
                          }
                        >
                          <span>
                            {
                              model.label
                            }
                            {" — "}
                            {
                              model.model
                            }
                          </span>
                        </SelectItem>
                      ),
                    )
                  }
                </SelectContent>
              </Select>
            </div>
          </CardHeader>


          {/* ================================================
              CHAT AREA
          ================================================ */}

          <ScrollArea
            className="
              flex-1
            "
          >
            <div
              className="
                mx-auto
                flex
                min-h-[58vh]
                max-w-5xl
                flex-col
                px-4
                py-7
                md:px-8
              "
            >
              {/* ============================================
                  EMPTY STATE
              ============================================ */}

              {
                messages.length === 0
                  ? (
                    <div
                      className="
                        m-auto
                        w-full
                        max-w-3xl
                        py-12
                        text-center
                      "
                    >
                      <div
                        className="
                          mx-auto
                          mb-5
                          grid
                          size-16
                          place-items-center
                          rounded-3xl
                          bg-primary/10
                          text-primary
                        "
                      >
                        <Bot
                          className="
                            size-8
                          "
                        />
                      </div>

                      <h1
                        className="
                          text-2xl
                          font-semibold
                          tracking-tight
                          md:text-3xl
                        "
                      >
                        How can
                        Reliance Digital
                        help today?
                      </h1>

                      <p
                        className="
                          mx-auto
                          mt-3
                          max-w-xl
                          text-sm
                          leading-6
                          text-muted-foreground
                          md:text-base
                        "
                      >
                        Ask about
                        products,
                        pricing,
                        orders,
                        resQ service,
                        manuals or
                        troubleshooting.
                      </p>


                      {/* ====================================
                          SUGGESTED PROMPTS
                      ==================================== */}

                      <div
                        className="
                          mt-7
                          grid
                          gap-3
                          sm:grid-cols-2
                        "
                      >
                        {
                          SUGGESTED_PROMPTS
                            .map(
                              (prompt) => (
                                <button
                                  key={
                                    prompt
                                  }

                                  type="button"

                                  onClick={
                                    () => {
                                      setInput(
                                        prompt,
                                      )
                                    }
                                  }

                                  className="
                                    rounded-2xl
                                    border
                                    bg-card
                                    p-4
                                    text-left
                                    text-sm
                                    transition
                                    hover:-translate-y-0.5
                                    hover:border-primary/30
                                    hover:shadow-md
                                  "
                                >
                                  {
                                    prompt
                                  }
                                </button>
                              ),
                            )
                        }
                      </div>
                    </div>
                  )
                  : (
                    // =======================================
                    // CHAT MESSAGES
                    // =======================================

                    <div
                      className="
                        space-y-6
                      "
                    >
                      {
                        messages.map(
                          (message) => (
                            <div
                              key={
                                message.id
                              }

                              className={
                                `flex ${
                                  message.role
                                  === "user"
                                    ? "justify-end"
                                    : "justify-start"
                                }`
                              }
                            >
                              <div
                                className={
                                  `
                                    max-w-[90%]
                                    rounded-3xl
                                    px-5
                                    py-4
                                    text-sm
                                    leading-7
                                    md:max-w-[78%]

                                    ${
                                      message.role
                                      === "user"
                                        ? `
                                          rounded-br-lg
                                          bg-primary
                                          text-primary-foreground
                                        `
                                        : `
                                          rounded-bl-lg
                                          border
                                          bg-card
                                          text-card-foreground
                                          shadow-sm
                                        `
                                    }
                                  `
                                }
                              >
                                {/* ==========================
                                    AGENT BADGE
                                ========================== */}

                                {
                                  message.role
                                  === "assistant"
                                  &&
                                  (
                                    <div
                                      className="
                                        mb-3
                                        flex
                                        items-center
                                        gap-2
                                      "
                                    >
                                      <AgentBadge
                                        agent={
                                          message.agent
                                        }
                                      />

                                      {
                                        message.actualProvider
                                        && (
                                          <Badge
                                            variant="outline"
                                            title="Requested provider ? actual provider"
                                            className="
                                              rounded-full
                                              px-2.5
                                              py-1
                                              text-[11px]
                                              font-normal
                                            "
                                          >
                                            {
                                              PROVIDER_LABELS[
                                                message.requestedProvider
                                                ?? "auto"
                                              ]
                                              ?? message.requestedProvider
                                              ?? "Auto"
                                            }

                                            {" -> "}

                                            {
                                              PROVIDER_LABELS[
                                                message.actualProvider
                                              ]
                                              ?? message.actualProvider
                                            }
                                          </Badge>
                                        )
                                      }


                                      {
                                        isStreaming
                                        &&
                                        !message.content
                                        &&
                                        (
                                          <LoaderCircle
                                            className="
                                              size-4
                                              animate-spin
                                              text-muted-foreground
                                            "
                                          />
                                        )
                                      }
                                    </div>
                                  )
                                }


                                {/* ==========================
                                    IMAGE PREVIEW
                                ========================== */}

                                {
                                  message.imagePreview
                                  &&
                                  (
                                    <div
                                      className="
                                        mb-4
                                        overflow-hidden
                                        rounded-2xl
                                        border
                                        bg-black/5
                                      "
                                    >
                                      {/* eslint-disable-next-line @next/next/no-img-element */}
                                      <img
                                        src={
                                          message.imagePreview
                                        }

                                        alt={
                                          message.imageName
                                          ??
                                          "Uploaded image"
                                        }

                                        className="
                                          max-h-72
                                          w-full
                                          object-contain
                                        "
                                      />
                                    </div>
                                  )
                                }


                                {/* ==========================
                                    MESSAGE TEXT
                                ========================== */}

                                <div
  className="
    break-words
    text-sm
    leading-7
  "
>
  {
    message.content
      ? (
          message.role === "assistant"
            ? (
                <ReactMarkdown
                  components={{
                    p: ({ children }) => (
                      <p className="mb-3 last:mb-0">
                        {children}
                      </p>
                    ),

                    strong: ({ children }) => (
                      <strong className="font-semibold">
                        {children}
                      </strong>
                    ),

                    ul: ({ children }) => (
                      <ul className="my-3 list-disc space-y-1 pl-5">
                        {children}
                      </ul>
                    ),

                    ol: ({ children }) => (
                      <ol className="my-3 list-decimal space-y-1 pl-5">
                        {children}
                      </ol>
                    ),

                    li: ({ children }) => (
                      <li>
                        {children}
                      </li>
                    ),

                    code: ({ children }) => (
                      <code
                        className="
                          rounded
                          bg-black/5
                          px-1
                          py-0.5
                          font-mono
                          text-[0.9em]
                        "
                      >
                        {children}
                      </code>
                    ),
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )
            : (
                <div className="whitespace-pre-wrap">
                  {message.content}
                </div>
              )
        )
      : (
          message.role === "assistant"
            ? "Thinking..."
            : ""
        )
  }
</div>
                                {/*
                                  IMPORTANT:

                                  No Sources UI here.

                                  RAG still works internally,
                                  but file paths / citations
                                  are not displayed to user.
                                */}
                              </div>
                            </div>
                          ),
                        )
                      }

                      <div
                        ref={endRef}
                      />
                    </div>
                  )
              }
            </div>
          </ScrollArea>


          {/* ================================================
              COMPOSER
          ================================================ */}

          <div
            className="
              border-t
              bg-white/85
              p-3
              md:p-4
            "
          >
            <div
              className="
                mx-auto
                max-w-5xl
              "
            >
              {/* ============================================
                  ERROR
              ============================================ */}

              {
                error
                &&
                (
                  <div
                    className="
                      mb-3
                      rounded-2xl
                      border
                      border-destructive/20
                      bg-destructive/5
                      px-4
                      py-2.5
                      text-sm
                      text-destructive
                    "
                  >
                    {error}
                  </div>
                )
              }


              {/* ============================================
                  ATTACHED IMAGE
              ============================================ */}

              {
                image
                &&
                (
                  <div
                    className="
                      mb-3
                      flex
                      items-center
                      gap-3
                      rounded-2xl
                      border
                      bg-muted/50
                      p-3
                    "
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={
                        image.data_url
                      }

                      alt={
                        image.name
                      }

                      className="
                        size-14
                        rounded-xl
                        object-cover
                      "
                    />

                    <div
                      className="
                        min-w-0
                        flex-1
                      "
                    >
                      <div
                        className="
                          flex
                          items-center
                          gap-2
                        "
                      >
                        <ImageIcon
                          className="
                            size-4
                            text-muted-foreground
                          "
                        />

                        <p
                          className="
                            truncate
                            text-sm
                            font-medium
                          "
                        >
                          {
                            image.name
                          }
                        </p>
                      </div>

                      <label
                        className="
                          mt-1.5
                          flex
                          cursor-pointer
                          items-center
                          gap-2
                          text-xs
                          text-muted-foreground
                        "
                      >
                        <input
                          type="checkbox"

                          checked={
                            ingestImage
                          }

                          onChange={
                            (event) => {
                              setIngestImage(
                                event
                                  .target
                                  .checked,
                              )
                            }
                          }

                          className="
                            size-3.5
                            accent-current
                          "
                        />

                        Add this image
                        to the demo knowledge base
                        base
                      </label>
                    </div>

                    <Button
                      type="button"

                      variant="ghost"

                      size="icon"

                      onClick={
                        () => {
                          setImage(null)
                        }
                      }
                    >
                      <X
                        className="
                          size-4
                        "
                      />
                    </Button>
                  </div>
                )
              }


              {/* ============================================
                  MESSAGE FORM
              ============================================ */}

              <form
                onSubmit={
                  handleSubmit
                }

                className="
                  rounded-3xl
                  border
                  bg-card
                  p-2
                  shadow-sm
                  transition
                  focus-within:ring-2
                  focus-within:ring-ring/20
                "
              >
                <Textarea
                  value={input}

                  onChange={
                    (event) => {
                      setInput(
                        event
                          .target
                          .value,
                      )
                    }
                  }

                  onKeyDown={
                    (event) => {
                      if (
                        event.key
                        === "Enter"
                        &&
                        !event.shiftKey
                      ) {
                        event
                          .preventDefault()

                        event
                          .currentTarget
                          .form
                          ?.requestSubmit()
                      }
                    }
                  }

                  placeholder={
                    "Ask about products, orders, resQ, warranty or manuals..."
                  }

                  className="
                    min-h-24
                    resize-none
                    border-0
                    bg-transparent
                    px-3
                    py-3
                    shadow-none
                    focus-visible:ring-0
                  "

                  disabled={
                    isStreaming
                  }
                />


                <div
                  className="
                    flex
                    items-center
                    justify-between
                    gap-2
                    px-1
                    pb-1
                  "
                >
                  {/* ========================================
                      LEFT ACTIONS
                  ======================================== */}

                  <div
                    className="
                      flex
                      min-w-0
                      items-center
                      gap-2
                    "
                  >
                    <input
                      ref={
                        fileInputRef
                      }

                      type="file"

                      accept="
                        image/png,
                        image/jpeg,
                        image/webp
                      "

                      className="
                        hidden
                      "

                      onChange={
                        (event) => {
                          void handleImage(
                            event
                              .target
                              .files?.[0],
                          )

                          event
                            .currentTarget
                            .value = ""
                        }
                      }
                    />

                    <Button
                      type="button"

                      variant="ghost"

                      size="sm"

                      className="
                        gap-2
                      "

                      onClick={
                        () => {
                          fileInputRef
                            .current
                            ?.click()
                        }
                      }

                      disabled={
                        isStreaming
                      }
                    >
                      <Paperclip
                        className="
                          size-4
                        "
                      />

                      <span
                        className="
                          hidden
                          sm:inline
                        "
                      >
                        Attach image
                      </span>
                    </Button>


                    <Badge
                      variant="outline"

                      className="
                        hidden
                        max-w-[190px]
                        truncate
                        font-normal
                        md:inline-flex
                      "
                    >
                      {
                        selectedModel.model
                      }
                    </Badge>
                  </div>


                  {/* ========================================
                      SEND BUTTON
                  ======================================== */}

                  <Button
                    type="submit"

                    size="icon"

                    disabled={
                      isStreaming
                      ||
                      (
                        !input.trim()
                        &&
                        !image
                      )
                    }
                  >
                    {
                      isStreaming
                        ? (
                          <LoaderCircle
                            className="
                              size-4
                              animate-spin
                            "
                          />
                        )
                        : (
                          <Send
                            className="
                              size-4
                            "
                          />
                        )
                    }
                  </Button>
                </div>
              </form>


              <p
                className="
                  mt-2
                  text-center
                  text-[11px]
                  text-muted-foreground
                "
              >
                Reliance Digital
                hackathon demo.
                Product and service
                records are mock data.
              </p>
            </div>
          </div>
        </Card>


        {/* ==================================================
            FEATURED PRODUCTS SIDEBAR
        ================================================== */}

        <aside
          className="
            hidden
            xl:block
          "
        >
          <Card
            className="
              sticky
              top-5
              border-black/5
              bg-white/90
              shadow-lg
              backdrop-blur
            "
          >
            <CardHeader>
              <div
                className="
                  flex
                  items-center
                  gap-3
                "
              >
                <div
                  className="
                    grid
                    size-10
                    place-items-center
                    rounded-2xl
                    bg-primary/10
                    text-primary
                  "
                >
                  <ShoppingBag
                    className="
                      size-4
                    "
                  />
                </div>

                <div>
                  <CardTitle
                    className="
                      text-base
                    "
                  >
                    Featured products
                  </CardTitle>

                  <p
                    className="
                      mt-0.5
                      text-xs
                      text-muted-foreground
                    "
                  >
                    Reliance Digital
                    demo catalog
                  </p>
                </div>
              </div>
            </CardHeader>


            <CardContent
              className="
                space-y-3
              "
            >
              {
                products.map(
                  (
                    product,
                    index,
                  ) => (
                    <div
                      key={
                        product.id
                      }
                    >
                      <div
                        className="
                          rounded-2xl
                          p-2
                          transition
                          hover:bg-muted/60
                        "
                      >
                        <div
                          className="
                            flex
                            items-start
                            justify-between
                            gap-3
                          "
                        >
                          <Badge
                            variant="outline"

                            className="
                              font-mono
                              text-[10px]
                            "
                          >
                            {
                              product.id
                            }
                          </Badge>

                          <span
                            className="
                              whitespace-nowrap
                              text-sm
                              font-semibold
                              text-primary
                            "
                          >
                            {
                              product.price
                            }
                          </span>
                        </div>

                        <p
                          className="
                            mt-2
                            text-sm
                            font-medium
                            leading-5
                          "
                        >
                          {
                            product.name
                          }
                        </p>

                        <p
                          className="
                            mt-1
                            text-xs
                            text-muted-foreground
                          "
                        >
                          {
                            product.warranty
                          }
                        </p>
                      </div>


                      {
                        index
                        <
                        products.length
                        - 1
                        &&
                        (
                          <Separator
                            className="
                              mt-3
                            "
                          />
                        )
                      }
                    </div>
                  ),
                )
              }
            </CardContent>
          </Card>
        </aside>
      </div>
    </main>
  )
}
