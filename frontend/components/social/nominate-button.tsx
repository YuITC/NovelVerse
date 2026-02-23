"use client"

import { useEffect, useState } from "react"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { NominationStatus } from "@/lib/types/social"

interface NominateButtonProps {
  novelId: string
}

export function NominateButton({ novelId }: NominateButtonProps) {
  const { user } = useUser()
  const [status, setStatus] = useState<NominationStatus | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!user) return
    apiFetch<NominationStatus>(`/novels/${novelId}/nominate`)
      .then(setStatus)
      .catch(() => null)
  }, [user, novelId])

  if (!user) return null

  async function handleToggle() {
    setLoading(true)
    try {
      const next = await apiFetch<NominationStatus>(`/novels/${novelId}/nominate`, { method: "POST" })
      setStatus(next)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const isNominated = status?.is_nominated ?? false
  const remaining = status?.nominations_remaining ?? 0

  return (
    <Button
      size="sm"
      variant={isNominated ? "default" : "outline"}
      onClick={handleToggle}
      disabled={loading}
    >
      {isNominated ? "⭐ Đã đề cử" : `⭐ Đề cử (${remaining})`}
    </Button>
  )
}
