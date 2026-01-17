'use client'

import { useEffect, useState } from 'react'
import Header from '../../components/Header'
import { apiFetch } from '../lib/api'

const categories = ['전체', '정치', '경제', '사회', '세계', 'IT/과학', '문화', '스포츠']

interface PopularTopic {
  topic_id: string
  title?: string
  category?: string
  popularity_count: number
  newsletter_id?: string
  newsletter_text?: string
  created_at?: string
}

export default function PopularPage() {
  const [selected, setSelected] = useState('전체')
  const [items, setItems] = useState<PopularTopic[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    const categoryQuery = selected === '전체' ? '' : `?category=${encodeURIComponent(selected)}`
    apiFetch(`/topics/popular${categoryQuery}`)
      .then((data) => setItems(data.items || []))
      .catch((err: any) => setError(err.message))
  }, [selected])

  return (
    <main className="mx-auto max-w-5xl">
      <Header />
      <section className="section-card rounded-3xl p-6">
        <h2 className="text-xl font-serif">카테고리별 인기 주제</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              className={`rounded-full px-4 py-2 text-xs ${
                selected === category
                  ? 'bg-moss text-white'
                  : 'border border-moss/30 bg-white text-ink'
              }`}
              onClick={() => setSelected(category)}
            >
              {category}
            </button>
          ))}
        </div>
        {error && <p className="mt-4 text-sm text-ember">{error}</p>}
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {items.map((item) => (
            <article key={item.topic_id} className="rounded-2xl border border-moss/20 bg-white/80 p-4">
              <div className="text-xs text-ink/60">{item.category || '기타'} · 기사 {item.popularity_count}건</div>
              <h3 className="mt-2 text-lg font-serif">{item.title || '주요 이슈'}</h3>
              {item.newsletter_text && (
                <p className="mt-2 text-sm text-ink/80 whitespace-pre-wrap">{item.newsletter_text}</p>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
