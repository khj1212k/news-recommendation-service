'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { apiFetch } from '../lib/api'

const categories = ['정치', '경제', '사회', '세계', 'IT/과학', '문화', '스포츠']

export default function OnboardingPage() {
  const router = useRouter()
  const [selected, setSelected] = useState<string[]>([])
  const [keywords, setKeywords] = useState('')
  const [error, setError] = useState('')

  function toggleCategory(category: string) {
    setSelected((prev) =>
      prev.includes(category) ? prev.filter((item) => item !== category) : [...prev, category]
    )
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    try {
      await apiFetch('/me/preferences', {
        method: 'POST',
        body: JSON.stringify({
          categories: selected,
          keywords: keywords
            .split(',')
            .map((k) => k.trim())
            .filter(Boolean),
        }),
      })
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <main className="mx-auto max-w-3xl">
      <section className="section-card rounded-3xl p-8">
        <h1 className="text-2xl font-serif">관심사 설정</h1>
        <p className="mt-2 text-sm text-ink/70">
          원하는 분야와 키워드를 고르면 개인 맞춤 뉴스레터가 만들어집니다.
        </p>
        <form className="mt-6 space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-3 md:grid-cols-3">
            {categories.map((category) => (
              <button
                type="button"
                key={category}
                onClick={() => toggleCategory(category)}
                className={`rounded-2xl border px-4 py-3 text-sm ${
                  selected.includes(category)
                    ? 'border-moss bg-moss text-white'
                    : 'border-moss/30 bg-white text-ink'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
          <div>
            <label className="text-sm text-ink/70">키워드 (쉼표로 구분)</label>
            <input
              className="mt-2 w-full rounded-2xl border border-moss/30 bg-white px-4 py-3"
              placeholder="예: AI, 스타트업, 지역 교통"
              value={keywords}
              onChange={(event) => setKeywords(event.target.value)}
            />
          </div>
          {error && <p className="text-sm text-ember">{error}</p>}
          <button className="rounded-2xl bg-ember px-6 py-3 text-white">저장하고 시작</button>
        </form>
      </section>
    </main>
  )
}
