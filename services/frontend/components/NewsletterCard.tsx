'use client'

import Link from 'next/link'
import { apiFetch } from '../app/lib/api'
import FeedbackButtons from './FeedbackButtons'

interface Props {
  item: {
    newsletter_id: string
    topic_id: string
    title?: string
    category?: string
    newsletter_text: string
    created_at: string
    popularity_count: number
    reason: string
  }
  rankPosition?: number
}

export default function NewsletterCard({ item, rankPosition }: Props) {
  return (
    <article className="section-card fade-in rounded-3xl p-6 shadow-glow">
      <div className="flex flex-wrap items-center gap-3 text-xs text-ink/60">
        <span className="rounded-full bg-haze px-3 py-1">{item.category || '기타'}</span>
        <span>인기 기사 {item.popularity_count}건</span>
        <span>{new Date(item.created_at).toLocaleString('ko-KR')}</span>
      </div>
      <h2 className="mt-4 text-xl font-serif text-ink">{item.title || '주요 이슈'}</h2>
      <p className="mt-3 text-sm text-ink/80 whitespace-pre-wrap">{item.newsletter_text}</p>
      <p className="mt-4 text-xs text-ember">왜 추천했나요? {item.reason}</p>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Link
          className="rounded-full bg-moss px-4 py-2 text-xs text-white"
          href={`/newsletter/${item.newsletter_id}`}
          onClick={() =>
            apiFetch('/events', {
              method: 'POST',
              body: JSON.stringify({
                event_type: 'click',
                newsletter_id: item.newsletter_id,
                topic_id: item.topic_id,
                context: { page: 'feed', rank_position: rankPosition },
              }),
            }).catch(() => undefined)
          }
        >
          자세히 읽기
        </Link>
        <FeedbackButtons topicId={item.topic_id} newsletterId={item.newsletter_id} />
      </div>
    </article>
  )
}
