'use client'

import { apiFetch } from '../app/lib/api'

interface Props {
  topicId: string
  newsletterId: string
}

export default function FeedbackButtons({ topicId, newsletterId }: Props) {
  async function sendEvent(eventType: string) {
    try {
      await apiFetch('/events', {
        method: 'POST',
        body: JSON.stringify({ event_type: eventType, topic_id: topicId, newsletter_id: newsletterId }),
      })
    } catch (error) {
      console.error(error)
    }
  }

  return (
    <div className="flex flex-wrap gap-2 text-xs">
      <button className="rounded-full border border-moss/30 px-3 py-1 text-moss" onClick={() => sendEvent('follow')}>
        주제 팔로우
      </button>
      <button className="rounded-full border border-moss/30 px-3 py-1 text-moss" onClick={() => sendEvent('save')}>
        뉴스레터 저장
      </button>
      <button className="rounded-full border border-ember/40 px-3 py-1 text-ember" onClick={() => sendEvent('hide')}>
        이 주제 숨기기
      </button>
    </div>
  )
}
