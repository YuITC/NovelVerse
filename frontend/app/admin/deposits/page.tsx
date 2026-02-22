"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { AdminDeposit } from "@/lib/types/admin"

function formatNum(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

export default function AdminDepositsPage() {
  const [deposits, setDeposits] = useState<AdminDeposit[]>([])
  const [statusFilter, setStatusFilter] = useState<string>("pending")
  const [confirmAmounts, setConfirmAmounts] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  async function load() {
    const data = await apiFetch<AdminDeposit[]>(`/admin/deposits?status=${statusFilter}`)
    setDeposits(data)
  }

  useEffect(() => { load() }, [statusFilter])

  async function handleConfirm(depositId: string) {
    const amountStr = confirmAmounts[depositId]
    if (!amountStr) { setMessage("Nhập số tiền nhận được"); return }
    const amount = parseInt(amountStr.replace(/\D/g, ""), 10)
    if (amount < 5000) { setMessage("Số tiền tối thiểu 5.000đ"); return }
    setLoading(depositId)
    try {
      await apiFetch(`/admin/deposits/${depositId}/confirm`, {
        method: "PATCH",
        body: JSON.stringify({ amount_vnd_received: amount }),
      })
      setMessage("Đã xác nhận!")
      await load()
    } catch { setMessage("Lỗi khi xác nhận") }
    finally { setLoading(null); setTimeout(() => setMessage(null), 3000) }
  }

  async function handleReject(depositId: string) {
    if (!confirm("Từ chối yêu cầu nạp tiền này?")) return
    setLoading("reject-" + depositId)
    try {
      await apiFetch(`/admin/deposits/${depositId}/reject`, { method: "PATCH", body: JSON.stringify({}) })
      setMessage("Đã từ chối")
      await load()
    } catch { setMessage("Lỗi") }
    finally { setLoading(null); setTimeout(() => setMessage(null), 3000) }
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Quản lý Nạp tiền</h1>
      <div className="flex gap-2">
        {["pending", "completed", "rejected"].map((s) => (
          <Button key={s} variant={statusFilter === s ? "default" : "outline"} size="sm"
            onClick={() => setStatusFilter(s)}>
            {s === "pending" ? "Chờ xử lý" : s === "completed" ? "Đã xác nhận" : "Đã từ chối"}
          </Button>
        ))}
      </div>
      {message && <p className="text-sm text-green-600">{message}</p>}
      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="px-4 py-2 text-left">Mã CK</th>
              <th className="px-4 py-2 text-left">User</th>
              <th className="px-4 py-2 text-right">Số tiền yêu cầu</th>
              <th className="px-4 py-2 text-left">Thời gian</th>
              {statusFilter === "pending" && <th className="px-4 py-2">Hành động</th>}
            </tr>
          </thead>
          <tbody>
            {deposits.map((d) => (
              <tr key={d.id} className="border-t">
                <td className="px-4 py-3 font-mono font-bold">{d.transfer_code}</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{d.user_id.slice(0, 8)}...</td>
                <td className="px-4 py-3 text-right">{formatNum(d.amount_vnd)}đ</td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{new Date(d.created_at).toLocaleString("vi-VN")}</td>
                {statusFilter === "pending" && (
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Thực nhận (VND)"
                        value={confirmAmounts[d.id] ?? ""}
                        onChange={(e) => setConfirmAmounts((prev) => ({ ...prev, [d.id]: e.target.value }))}
                        className="w-32 rounded border px-2 py-1 text-xs"
                      />
                      <Button size="sm" onClick={() => handleConfirm(d.id)} disabled={loading === d.id}>
                        Xác nhận
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleReject(d.id)}
                        disabled={loading === "reject-" + d.id}>
                        Từ chối
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {deposits.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">Không có yêu cầu nào</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
