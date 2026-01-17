'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import Header from '../../../components/Header'
import FeedbackButtons from '../../../components/FeedbackButtons'
import { apiFetch } from '../../lib/api'

interface Citation {
  sentence_index: number
  source_article_id: string
  source_excerpt: string
  source_offset_start?: number
  source_offset_end?: number
}

interface Source {
  id: string
  url: string
  title?: string
  publisher?: string
  published_at?: string
}

interface NewsletterDetail {
  id: string
  topic_id: string
  category?: string
  title?: string
  newsletter_text: string
  created_at: string
  citations: Citation[]
  sources: Source[]
}

export default function NewsletterPage() {
  const params = useParams()
  const [detail, setDetail] = useState<NewsletterDetail | null>(null)
  const [error, setError] = useState('')
  const topicIdRef = useRef<string | null>(null)

  useEffect(() => {
    const newsletterId = params?.id as string
    if (!newsletterId) return
    const start = Date.now()
    apiFetch(`/newsletter/${newsletterId}`)
      .then((data) => {
        setDetail(data)
        topicIdRef.current = data.topic_id
        return apiFetch('/events', {
          method: 'POST',
          body: JSON.stringify({ event_type: 'impression', newsletter_id: newsletterId, topic_id: data.topic_id }),
        })
      })
      .catch((err: any) => setError(err.message))

    return () => {
      const dwellSeconds = Math.round((Date.now() - start) / 1000)
      if (newsletterId) {
        apiFetch('/events', {
          method: 'POST',
          body: JSON.stringify({
            event_type: 'dwell',
            newsletter_id: newsletterId,
            topic_id: topicIdRef.current,
            value: dwellSeconds,
          }),
        }).catch(() => undefined)
      }
    }
  }, [params?.id])

  if (error) {
    return <div className="text-ember">{error}</div>
  }

  return (
    <main className="mx-auto max-w-4xl">
      <Header />
      {detail && (
        <section className="section-card rounded-3xl p-8">
          <div className="text-xs text-ink/60">
            {detail.category || '기타'} · {new Date(detail.created_at).toLocaleString('ko-KR')}
          </div>
          <h1 className="mt-3 text-3xl font-serif">{detail.title || '주요 이슈'}</h1>
          <p className="mt-4 whitespace-pre-wrap text-sm text-ink/80">{detail.newsletter_text}</p>
          <div className="mt-6">
            <FeedbackButtons topicId={detail.topic_id} newsletterId={detail.id} />
          </div>
          <div className="mt-8 border-t border-moss/20 pt-6">
            <h2 className="text-lg font-serif">출처</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {detail.sources.map((source) => (
                <li key={source.id} className="flex flex-col gap-1">
                  <a
                    className="text-moss underline"
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={() =>
                      apiFetch('/events', {
                        method: 'POST',
                        body: JSON.stringify({
                          event_type: 'click',
                          newsletter_id: detail.id,
                          topic_id: detail.topic_id,
                          context: { source_id: source.id },
                        }),
                      }).catch(() => undefined)
                    }
                  >
                    {source.title || source.url}
                  </a>
                  <span className="text-xs text-ink/60">
                    {source.publisher} · {source.published_at ? new Date(source.published_at).toLocaleString('ko-KR') : ''}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-8 border-t border-moss/20 pt-6">
            <h2 className="text-lg font-serif">근거 문장</h2>
            <ul className="mt-3 space-y-2 text-sm text-ink/70">
              {detail.citations.map((citation, index) => (
                <li key={`${citation.source_article_id}-${index}`}>• {citation.source_excerpt}</li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </main>
  )
}
