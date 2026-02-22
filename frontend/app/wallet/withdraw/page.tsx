"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { WithdrawalRequest, Wallet } from "@/lib/types/economy"

function formatNum(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

export default function WithdrawPage() {
  const { user } = useUser()
  const router = useRouter()
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [history, setHistory] = useState<WithdrawalRequest[]>([])
  const [ttAmount, setTtAmount] = useState("")
  const [bankName, setBankName] = useState("")
  const [accountNumber, setAccountNumber] = useState("")
  const [accountHolder, setAccountHolder] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!user) { router.push("/"); return }
    const u = user as { role?: string }
    if (u.role !== "uploader" && u.role !== "admin") { router.push("/wallet"); return }
    Promise.all([
      apiFetch<Wallet>("/economy/wallet"),
      apiFetch<WithdrawalRequest[]>("/economy/withdrawal"),
    ]).then(([w, wrs]) => { setWallet(w); setHistory(wrs) }).catch(console.error)
  }, [user, router])

  const amount = parseFloat(ttAmount) || 0
  const vndEquiv = amount * 1

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (amount < 5000) { setError("Tối thiểu 5.000 Tiên Thạch"); return }
    if (!bankName || !accountNumber || !accountHolder) { setError("Vui lòng điền đầy đủ thông tin ngân hàng"); return }
    setLoading(true); setError(null)
    try {
      await apiFetch("/economy/withdrawal", {
        method: "POST",
        body: JSON.stringify({
          tt_amount: amount,
          bank_info: { bank_name: bankName, account_number: accountNumber, account_holder: accountHolder },
        }),
      })
      setSuccess(true)
      const [w, wrs] = await Promise.all([apiFetch<Wallet>("/economy/wallet"), apiFetch<WithdrawalRequest[]>("/economy/withdrawal")])
      setWallet(w); setHistory(wrs)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Không thể tạo yêu cầu rút tiền")
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="mx-auto max-w-lg px-4 py-8 space-y-6">
      <h1 className="text-2xl font-bold">🌕 Rút Tiên Thạch</h1>
      {wallet && (
        <div className="rounded-lg border p-4 bg-muted/30">
          <span className="text-muted-foreground text-sm">Số dư Tiên Thạch: </span>
          <span className="font-bold">{formatNum(wallet.tien_thach)} TT</span>
          <span className="text-sm text-muted-foreground ml-2">~ {formatNum(wallet.tien_thach)}đ</span>
        </div>
      )}

      {success && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/10 border border-green-200 p-4 text-sm text-green-700 dark:text-green-400">
          Yêu cầu rút tiền đã được gửi. Admin sẽ xử lý trong 1-3 ngày làm việc.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1">Số Tiên Thạch muốn rút (tối thiểu 5.000)</label>
          <input
            type="number" min={5000} step={1000}
            value={ttAmount} onChange={(e) => setTtAmount(e.target.value)}
            placeholder="Nhập số lượng..."
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {amount >= 5000 && <p className="text-xs text-muted-foreground mt-1">Sẽ nhận: {formatNum(vndEquiv)}đ</p>}
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">Ngân hàng</label>
          <input value={bankName} onChange={(e) => setBankName(e.target.value)} placeholder="VD: Vietcombank"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">Số tài khoản</label>
          <input value={accountNumber} onChange={(e) => setAccountNumber(e.target.value)} placeholder="1234567890"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">Chủ tài khoản</label>
          <input value={accountHolder} onChange={(e) => setAccountHolder(e.target.value)} placeholder="NGUYEN VAN A"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Đang gửi..." : "Gửi yêu cầu rút tiền"}
        </Button>
      </form>

      {history.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Lịch sử rút tiền</h2>
          <div className="space-y-2">
            {history.map((wr) => {
              const badgeClass = wr.status === "completed"
                ? "text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700"
                : wr.status === "rejected"
                ? "text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-700"
                : "text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700"
              const statusLabel = wr.status === "completed" ? "Hoàn tất" : wr.status === "rejected" ? "Từ chối" : "Đang xử lý"
              return (
                <div key={wr.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div>
                    <div>{formatNum(wr.tt_amount)} TT → {formatNum(wr.vnd_amount)}đ</div>
                    <div className="text-muted-foreground text-xs">{new Date(wr.created_at).toLocaleDateString("vi-VN")}</div>
                  </div>
                  <span className={badgeClass}>{statusLabel}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
