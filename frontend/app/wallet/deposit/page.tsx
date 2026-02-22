"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { DepositRequest } from "@/lib/types/economy"

const PRESET_AMOUNTS = [10000, 20000, 50000, 100000, 200000, 500000]

function formatVND(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n) + "đ"
}
function formatLT(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

export default function DepositPage() {
  const { user } = useUser()
  const router = useRouter()
  const [amount, setAmount] = useState<number>(50000)
  const [customAmount, setCustomAmount] = useState("")
  const [loading, setLoading] = useState(false)
  const [deposit, setDeposit] = useState<DepositRequest | null>(null)
  const [history, setHistory] = useState<DepositRequest[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) { router.push("/"); return }
    apiFetch<DepositRequest[]>("/economy/deposit").then(setHistory).catch(() => null)
  }, [user, router])

  const effectiveAmount = customAmount ? parseInt(customAmount.replace(/\D/g, ""), 10) || 0 : amount
  const ltToReceive = Math.round(effectiveAmount * 0.95)

  async function handleSubmit() {
    if (effectiveAmount < 5000) { setError("Số tiền tối thiểu là 5.000đ"); return }
    setLoading(true); setError(null)
    try {
      const d = await apiFetch<DepositRequest>("/economy/deposit", {
        method: "POST",
        body: JSON.stringify({ amount_vnd: effectiveAmount }),
      })
      setDeposit(d)
    } catch {
      setError("Không thể tạo yêu cầu nạp tiền. Vui lòng thử lại.")
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  if (deposit) {
    return (
      <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
        <h1 className="text-2xl font-bold">Thông tin chuyển khoản</h1>
        <div className="rounded-xl border p-6 space-y-4 bg-muted/30">
          <div className="grid grid-cols-2 gap-y-3 text-sm">
            <span className="text-muted-foreground">Ngân hàng</span>
            <span className="font-semibold">Vietcombank</span>
            <span className="text-muted-foreground">Số tài khoản</span>
            <span className="font-mono font-bold">1234567890</span>
            <span className="text-muted-foreground">Chủ tài khoản</span>
            <span className="font-semibold">NGUYEN VAN A</span>
            <span className="text-muted-foreground">Số tiền</span>
            <span className="font-bold text-lg">{formatVND(deposit.amount_vnd)}</span>
            <span className="text-muted-foreground">Nội dung CK</span>
            <span className="font-mono font-bold text-blue-600">{deposit.transfer_code}</span>
          </div>
          <div className="rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 p-3 text-sm text-amber-800 dark:text-amber-300">
            Vui lòng chuyển đúng nội dung chuyển khoản để hệ thống xử lý tự động.
            Sau khi chuyển, admin sẽ xác nhận trong vòng 24h.
          </div>
          <div className="text-sm text-muted-foreground">
            Sau khi xác nhận, bạn sẽ nhận được <strong>{formatLT(Math.round(deposit.amount_vnd * 0.95))} Linh Thạch</strong>.
          </div>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => router.push("/wallet")}>Về ví</Button>
          <Button variant="outline" onClick={() => setDeposit(null)}>Tạo yêu cầu mới</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      <h1 className="text-2xl font-bold">💎 Nạp Linh Thạch</h1>
      <p className="text-muted-foreground text-sm">1.000đ = 950 Linh Thạch (tỷ lệ 0.95)</p>

      <div className="grid grid-cols-3 gap-2">
        {PRESET_AMOUNTS.map((a) => {
          const isSelected = amount === a && !customAmount
          const btnClass = isSelected
            ? "rounded-lg border p-3 text-center text-sm font-medium transition-colors border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "rounded-lg border p-3 text-center text-sm font-medium transition-colors border-border hover:border-blue-300"
          return (
            <button
              key={a}
              onClick={() => { setAmount(a); setCustomAmount("") }}
              className={btnClass}
            >
              <div>{formatVND(a)}</div>
              <div className="text-xs text-muted-foreground">{formatLT(Math.round(a * 0.95))} LT</div>
            </button>
          )
        })}
      </div>

      <div>
        <label className="text-sm font-medium mb-1 block">Số tiền khác (VND)</label>
        <input
          type="text"
          placeholder="Nhập số tiền..."
          value={customAmount}
          onChange={(e) => { setCustomAmount(e.target.value); setAmount(0) }}
          className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {customAmount && effectiveAmount >= 5000 && (
          <p className="text-xs text-muted-foreground mt-1">Nhận được: {formatLT(ltToReceive)} Linh Thạch</p>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button className="w-full" onClick={handleSubmit} disabled={loading || effectiveAmount < 5000}>
        {loading ? "Đang tạo..." : "Nạp " + formatVND(effectiveAmount)}
      </Button>

      {history.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Lịch sử nạp tiền</h2>
          <div className="space-y-2">
            {history.slice(0, 5).map((d) => {
              const statusClass = d.status === "completed"
                ? "text-xs text-green-600"
                : d.status === "rejected"
                ? "text-xs text-red-600"
                : "text-xs text-amber-600"
              const statusLabel = d.status === "completed" ? "Đã xác nhận" : d.status === "rejected" ? "Từ chối" : "Đang chờ"
              return (
                <div key={d.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div>
                    <div className="font-mono text-xs">{d.transfer_code}</div>
                    <div className="text-muted-foreground">{new Date(d.created_at).toLocaleDateString("vi-VN")}</div>
                  </div>
                  <div className="text-right">
                    <div>{formatVND(d.amount_vnd)}</div>
                    <div className={statusClass}>{statusLabel}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
