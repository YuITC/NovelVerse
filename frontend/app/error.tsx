"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
      <div className="space-y-2">
        <h1 className="text-8xl font-bold text-muted-foreground">500</h1>
        <h2 className="text-2xl font-semibold">Đã xảy ra lỗi</h2>
        <p className="text-muted-foreground">
          Có lỗi không mong muốn xảy ra. Vui lòng thử lại.
        </p>
      </div>
      <Button onClick={reset}>Thử lại</Button>
    </div>
  )
}
