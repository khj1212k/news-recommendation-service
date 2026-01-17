'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { clearToken, getToken } from '../app/lib/storage'

export default function Header() {
  const [loggedIn, setLoggedIn] = useState(false)

  useEffect(() => {
    setLoggedIn(!!getToken())
  }, [])

  return (
    <header className="mb-10 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-3xl font-serif text-ink">뉴스 한눈에</h1>
        <p className="text-sm text-ink/70">한국 뉴스 추천 서비스 · 매일 4회 배치</p>
      </div>
      <nav className="flex flex-wrap gap-4 text-sm">
        <Link className="text-moss hover:text-ember" href="/">
          추천 피드
        </Link>
        <Link className="text-moss hover:text-ember" href="/popular">
          인기 주제
        </Link>
        <Link className="text-moss hover:text-ember" href="/onboarding">
          관심사 설정
        </Link>
        {loggedIn ? (
          <button
            className="text-ember"
            onClick={() => {
              clearToken()
              setLoggedIn(false)
            }}
          >
            로그아웃
          </button>
        ) : (
          <>
            <Link className="text-moss hover:text-ember" href="/login">
              로그인
            </Link>
            <Link className="text-moss hover:text-ember" href="/signup">
              회원가입
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}
