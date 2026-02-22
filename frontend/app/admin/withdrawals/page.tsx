"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { AdminWithdrawal } from "@/lib/types/admin"

function formatNum(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

export default function AdminWithdrawalsPage() {
  const [withdrawals, setWithdrawals] = useState<AdminWithdrawal[]>([])
  const [statusFilter, setStatusFilter] = useState<string>("pending")
  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  async function load() {
    const data = await apiFetch<AdminWithdrawal[]>(`/admin/withdrawals?status=${statusFilter}`)
    setWithdrawals(data)
  }

  useEffect(() => { load() }, [statusFilter])

  async function handleComplete(wrId: string) {
    if (!confirm("Đánh dấu đã chuyển khoản thành công?")) return
    setLoading(wrId)
    try {
      await apiFetch(`/admin/withdrawals/${wrId}/complete`, { method: "PATCH", body: JSON.stringify({}) })
      setMessage("Đã hoàn tất!")
      await load()
    } catch { setMessage("Lỗi") }
    finally { setLoading(null); setTimeout(() => setMessage(null), 3000) }
  }

  async function handleReject(wrId: string) {
    if (!confirm("Từ chối yêu cầu rút tiền này?")) return
    setLoading("reject-" + wrId)
    try {
      await apiFetch(`/admin/withdrawals/${wrId}/reject`, { method: "PATCH", body: JSON.stringify({}) })
      setMessage("Đã từ chối")
      await load()
    } catch { setMessage("Lỗi") }
    finally { setLoading(null); setTimeout(() => setMessage(null), 3000) }
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Quản lý Rút tiền</h1>
      <div className="flex gap-2">
        {["pending", "completed", "rejected"].map((s) => (
          <Button key={s} variant={statusFilter === s ? "default" : "outline"} size="sm"
            onClick={() => setStatusFilter(s)}>
            {s === "pending" ? "Chờ xử lý" : s === "completed" ? "Đã hoàn tất" : "Đã từ chối"}
          </Button>
        ))}
      </div>
      {message && <p className="text-sm text-green-600">{message}</p>}
      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="px-4 py-2 text-left">User</th>
              <th className="px-4 py-2 text-right">Số TT</th>
              <th className="px-4 py-2 text-right">VND</th>
              <th className="px-4 py-2 text-left">Ngân hàng</th>
              <th className="px-4 py-2 text-left">Thời gian</th>
              {statusFilter === "pending" && <th className="px-4 py-2">Hành động</th>}
            </tr>
          </thead>
          <tbody>
            {withdrawals.map((wr) => (
              <tr key={wr.id} className="border-t">
                <td className="px-4 py-3 text-xs text-muted-foreground">{wr.user_id.slice(0, 8)}...</td>
                <td className="px-4 py-3 text-right font-semibold">{formatNum(wr.tt_amount)} TT</td>
                <td className="px-4 py-3 text-right">{formatNum(wr.vnd_amount)}đ</td>
                <td className="px-4 py-3">
                  <div className="text-xs">
                    <div className="font-medium">{wr.bank_info.bank_name}</div>
                    <div className="font-mono">{wr.bank_info.account_number}</div>
                    <div className="text-muted-foreground">{wr.bank_info.account_holder}</div>
                  </div>
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">{new Date(wr.created_at).toLocaleString("vi-VN")}</td>
                {statusFilter === "pending" && (
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleComplete(wr.id)} disabled={loading === wr.id}>
                        Hoàn thành
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleReject(wr.id)}
                        disabled={loading === "reject-" + wr.id}>
                        Từ chối
                      </Button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
            {withdrawals.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Không có yêu cầu nào</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
