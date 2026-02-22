"use client"

import { useEffect, useState } from "react"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import type { ShopItem, Wallet } from "@/lib/types/economy"

function formatLT(n: number) {
  return new Intl.NumberFormat("vi-VN").format(n)
}

const ITEM_ICONS: Record<string, string> = {
  "Tẩy Tủy Dịch": "🧪",
  "Trúc Cơ Đan": "💊",
  "Dung Đan Quyết": "📜",
  "Khai Anh Pháp": "⚡",
  "Dưỡng Thần Hương": "🌸",
  "Hư Không Thạch": "💎",
  "Đạo Nguyên Châu": "⚪",
  "Đại Đạo Bia": "🏺",
  "Độ Kiếp Phù": "🔥",
  "Chân Tiên Lệnh": "👑",
}

export default function ShopPage() {
  const { user } = useUser()
  const [items, setItems] = useState<ShopItem[]>([])
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [giftTarget, setGiftTarget] = useState<string | null>(null)
  const [receiverId, setReceiverId] = useState("")
  const [loading, setLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  useEffect(() => {
    fetch("/api/v1/economy/shop").then((r) => r.json()).then(setItems).catch(console.error)
    if (user) {
      apiFetch<Wallet>("/economy/wallet").then(setWallet).catch(console.error)
    }
  }, [user])

  async function handlePurchase(item: ShopItem) {
    if (!user) { setMessage({ type: "error", text: "Đăng nhập để mua vật phẩm" }); return }
    setLoading(item.id)
    try {
      await apiFetch(`/economy/shop/${item.id}/purchase`, { method: "POST" })
      setMessage({ type: "success", text: "Đã mua " + item.name + "!" })
      const w = await apiFetch<Wallet>("/economy/wallet")
      setWallet(w)
    } catch {
      setMessage({ type: "error", text: "Không đủ Linh Thạch hoặc có lỗi xảy ra" })
    } finally {
      setLoading(null)
      setTimeout(() => setMessage(null), 3000)
    }
  }

  async function handleGift(item: ShopItem) {
    if (!receiverId.trim()) { setMessage({ type: "error", text: "Nhập ID người nhận" }); return }
    setLoading("gift-" + item.id)
    try {
      await apiFetch(`/economy/shop/${item.id}/gift`, {
        method: "POST",
        body: JSON.stringify({ receiver_id: receiverId.trim() }),
      })
      setMessage({ type: "success", text: "Đã tặng " + item.name + "!" })
      setGiftTarget(null)
      setReceiverId("")
      const w = await apiFetch<Wallet>("/economy/wallet")
      setWallet(w)
    } catch {
      setMessage({ type: "error", text: "Không thể tặng vật phẩm" })
    } finally {
      setLoading(null)
      setTimeout(() => setMessage(null), 3000)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">🛒 Thương Thành</h1>
        {wallet && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Số dư:</span>
            <span className="font-bold">💎 {formatLT(wallet.linh_thach)} LT</span>
          </div>
        )}
      </div>

      {message && (
        <div className={message.type === "success"
          ? "rounded-lg p-3 text-sm bg-green-50 dark:bg-green-900/10 text-green-700 dark:text-green-400"
          : "rounded-lg p-3 text-sm bg-red-50 dark:bg-red-900/10 text-red-700 dark:text-red-400"}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {items.map((item) => (
          <div key={item.id} className="rounded-xl border p-4 flex flex-col items-center gap-2 text-center hover:shadow-md transition-shadow">
            <span className="text-4xl">{ITEM_ICONS[item.name] ?? "🎁"}</span>
            <div className="font-medium text-sm leading-tight">{item.name}</div>
            <div className="text-xs text-blue-600 font-semibold">{formatLT(item.price_lt)} LT</div>
            <div className="flex flex-col gap-1 w-full mt-auto">
              <Button size="sm" variant="outline" className="w-full text-xs"
                onClick={() => handlePurchase(item)} disabled={loading === item.id}>
                {loading === item.id ? "..." : "Mua"}
              </Button>
              {giftTarget === item.id ? (
                <div className="flex gap-1">
                  <input placeholder="User ID" value={receiverId} onChange={(e) => setReceiverId(e.target.value)}
                    className="w-full rounded border px-1 py-0.5 text-xs" />
                  <Button size="sm" className="text-xs px-1" onClick={() => handleGift(item)}
                    disabled={loading === "gift-" + item.id}>✓</Button>
                  <Button size="sm" variant="ghost" className="text-xs px-1" onClick={() => setGiftTarget(null)}>✕</Button>
                </div>
              ) : (
                <Button size="sm" variant="ghost" className="w-full text-xs"
                  onClick={() => setGiftTarget(item.id)}>
                  Tặng
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
