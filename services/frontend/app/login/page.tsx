'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { publicFetch } from '../lib/api'
import { setToken } from '../lib/storage'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const response = await publicFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setToken(response.access_token)
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <main className="mx-auto max-w-xl">
      <section className="section-card rounded-3xl p-8">
        <h1 className="text-2xl font-serif">로그인</h1>
        <p className="mt-2 text-sm text-ink/70">
          계정으로 다시 접속하면 최신 추천 피드를 받을 수 있습니다.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <input
            className="w-full rounded-2xl border border-moss/30 bg-white px-4 py-3"
            placeholder="이메일"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="w-full rounded-2xl border border-moss/30 bg-white px-4 py-3"
            placeholder="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-sm text-ember">{error}</p>}
          <button className="w-full rounded-2xl bg-moss py-3 text-white">로그인</button>
        </form>
        <p className="mt-4 text-sm text-ink/70">
          아직 계정이 없으신가요?{' '}
          <Link className="text-moss hover:text-ember" href="/signup">
            회원가입
          </Link>
        </p>
      </section>
    </main>
  )
}
