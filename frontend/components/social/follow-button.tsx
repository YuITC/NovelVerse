"use client"

import { useEffect, useState } from "react"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { FollowStatus } from "@/lib/types/social"

interface FollowButtonProps {
  followeeId: string
}

export function FollowButton({ followeeId }: FollowButtonProps) {
  const { user } = useUser()
  const [status, setStatus] = useState<FollowStatus | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user || user.id === followeeId) return
    apiFetch<FollowStatus>(`/users/${followeeId}/follow`).then(setStatus).catch(() => null)
  }, [user, followeeId])

  if (!user || user.id === followeeId) return null

  async function handleToggle() {
    setLoading(true)
    try {
      const next = await apiFetch<FollowStatus>(`/users/${followeeId}/follow`, { method: "POST" })
      setStatus(next)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      size="sm"
      variant={status?.is_following ? "secondary" : "default"}
      onClick={handleToggle}
      disabled={loading}
    >
      {status?.is_following ? "Đang theo dõi" : "Theo dõi"}
      {status != null && (
        <span className="ml-1.5 text-xs opacity-70">{status.follower_count}</span>
      )}
    </Button>
  )
}
