"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { Wallet, Transaction } from "@/lib/types/economy"

function formatLT(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

const TX_TYPE_LABELS: Record<string, string> = {
  deposit: "Nạp Linh Thạch",
  vip_purchase: "Mua VIP",
  item_purchase: "Mua vật phẩm",
  gift_sent: "Tặng vật phẩm",
  gift_received: "Nhận vật phẩm",
  withdrawal: "Rút Tiên Thạch",
}

export default function WalletPage() {
  const { user } = useUser()
  const router = useRouter()
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { router.push("/"); return }
    Promise.all([
      apiFetch<Wallet>("/economy/wallet"),
      apiFetch<Transaction[]>("/economy/transactions?limit=20"),
    ]).then(([w, txs]) => {
      setWallet(w)
      setTransactions(txs)
    }).catch(console.error).finally(() => setLoading(false))
  }, [user, router])

  if (!user || loading) {
    return <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">Đang tải...</div>
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Ví của tôi</h1>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border p-5 space-y-1">
          <div className="text-sm text-muted-foreground">💎 Linh Thạch</div>
          <div className="text-2xl font-bold">{formatLT(wallet?.linh_thach ?? 0)}</div>
          <div className="text-xs text-muted-foreground">Dùng để mua VIP và vật phẩm</div>
          <Button size="sm" variant="outline" className="mt-2 w-full" onClick={() => router.push("/wallet/deposit")}>
            Nạp thêm
          </Button>
        </div>
        <div className="rounded-xl border p-5 space-y-1">
          <div className="text-sm text-muted-foreground">🌕 Tiên Thạch</div>
          <div className="text-2xl font-bold">{formatLT(wallet?.tien_thach ?? 0)}</div>
          <div className="text-xs text-muted-foreground">Kiếm từ tặng vật phẩm, rút về tiền</div>
          {(user as { role?: string })?.role === "uploader" || (user as { role?: string })?.role === "admin" ? (
            <Button size="sm" variant="outline" className="mt-2 w-full" onClick={() => router.push("/wallet/withdraw")}>
              Rút tiền
            </Button>
          ) : (
            <div className="mt-2 text-xs text-muted-foreground">Chỉ uploader mới rút được</div>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <Button variant="outline" onClick={() => router.push("/shop")}>🛒 Thương Thành</Button>
        <Button variant="outline" onClick={() => router.push("/vip")}>👑 VIP</Button>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Lịch sử giao dịch</h2>
        {transactions.length === 0 ? (
          <p className="text-muted-foreground text-sm">Chưa có giao dịch nào.</p>
        ) : (
          <div className="space-y-2">
            {transactions.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="font-medium text-sm">{TX_TYPE_LABELS[tx.transaction_type] ?? tx.transaction_type}</div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(tx.created_at).toLocaleString("vi-VN")} · {tx.currency_type === "linh_thach" ? "💎 LT" : "🌕 TT"}
                  </div>
                </div>
                <div className={`font-semibold ${tx.amount >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {tx.amount >= 0 ? "+" : ""}{formatLT(tx.amount)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
