"use client"

import { useEffect, useState } from "react"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { BookmarkStatus } from "@/lib/types/social"

interface BookmarkButtonProps {
  novelId: string
}

export function BookmarkButton({ novelId }: BookmarkButtonProps) {
  const { user } = useUser()
  const [bookmarked, setBookmarked] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user) return
    apiFetch<BookmarkStatus>(`/novels/${novelId}/bookmark`)
      .then((s) => setBookmarked(s.is_bookmarked))
      .catch(() => null)
  }, [user, novelId])

  if (!user) return null

  async function handleToggle() {
    setLoading(true)
    try {
      const next = await apiFetch<BookmarkStatus>(`/novels/${novelId}/bookmark`, { method: "POST" })
      setBookmarked(next.is_bookmarked)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button size="sm" variant="outline" onClick={handleToggle} disabled={loading}>
      {bookmarked ? "🔖 Đã lưu" : "🔖 Lưu truyện"}
    </Button>
  )
}
