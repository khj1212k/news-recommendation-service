'use client'

import { useEffect, useRef, useState } from 'react'
import Header from '../components/Header'
import NewsletterCard from '../components/NewsletterCard'
import { apiFetch } from './lib/api'
import { getToken } from './lib/storage'

interface FeedItem {
  newsletter_id: string
  topic_id: string
  title?: string
  category?: string
  newsletter_text: string
  created_at: string
  popularity_count: number
  reason: string
}

export default function HomePage() {
  const [items, setItems] = useState<FeedItem[]>([])
  const [error, setError] = useState('')
  const sentImpressions = useRef(new Set<string>())

  useEffect(() => {
    if (!getToken()) {
      setError('로그인이 필요합니다.')
      return
    }
    apiFetch('/feed')
      .then((data) => setItems(data.items || []))
      .catch((err: any) => setError(err.message))
  }, [])

  useEffect(() => {
    items.forEach((item, index) => {
      if (sentImpressions.current.has(item.newsletter_id)) return
      sentImpressions.current.add(item.newsletter_id)
      apiFetch('/events', {
        method: 'POST',
        body: JSON.stringify({
          event_type: 'impression',
          newsletter_id: item.newsletter_id,
          topic_id: item.topic_id,
          context: { page: 'feed', rank_position: index + 1 },
        }),
      }).catch(() => undefined)
    })
  }, [items])

  return (
    <main className="mx-auto max-w-5xl">
      <Header />
      <section className="grid gap-6">
        {error && (
          <div className="section-card rounded-3xl p-6 text-sm text-ember">
            {error} /login 또는 /signup에서 시작하세요.
          </div>
        )}
        {!error && items.length === 0 && (
          <div className="section-card rounded-3xl p-6 text-sm text-ink/70">
            추천 피드를 준비 중입니다. 잠시 후 다시 시도해 주세요.
          </div>
        )}
        {items.map((item, index) => (
          <NewsletterCard key={item.newsletter_id} item={item} rankPosition={index + 1} />
        ))}
      </section>
    </main>
  )
}
