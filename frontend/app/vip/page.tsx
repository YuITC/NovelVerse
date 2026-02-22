"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { VipBadge } from "@/components/vip/vip-badge"
import type { VipSubscription, SystemSettings } from "@/lib/types/vip"
import type { Wallet } from "@/lib/types/economy"

const PRO_FEATURES = [
  "Đọc sớm 3 ngày trước độc giả thường",
  "Trải nghiệm không quảng cáo",
  "Huy hiệu VIP Pro độc quyền",
  "Hỗ trợ qua email",
]

const MAX_FEATURES = [
  "Đọc sớm 7 ngày trước độc giả thường",
  "Trải nghiệm không quảng cáo",
  "Huy hiệu VIP Max độc quyền",
  "Hỗ trợ ưu tiên 24/7",
]

function formatLT(n: number | string): string {
  const num = typeof n === "string" ? parseFloat(n) : n
  return new Intl.NumberFormat("vi-VN").format(num)
}

export default function VipPage() {
  const { user } = useUser()
  const router = useRouter()
  const [settings, setSettings] = useState<SystemSettings | null>(null)
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [currentVip, setCurrentVip] = useState<VipSubscription | null>(null)
  const [selectedTier, setSelectedTier] = useState<"pro" | "max" | null>(null)
  const [purchasing, setPurchasing] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch("/api/v1/settings")
      .then((r) => r.ok ? r.json() : null)
      .then((data) => setSettings(data))
      .catch(() => null)
  }, [])

  useEffect(() => {
    if (!user) return
    apiFetch<VipSubscription[]>("/vip/me").then((subs) => {
      const active = subs.find((s) => s.status === "active")
      if (active) setCurrentVip(active)
    }).catch(() => null)
    apiFetch<Wallet>("/economy/wallet").then((w) => setWallet(w)).catch(() => null)
  }, [user])

  const proPriceLT = parseFloat(settings?.vip_pro_price_lt ?? "50000")
  const maxPriceLT = parseFloat(settings?.vip_max_price_lt ?? "100000")
  const ltBalance = wallet?.linh_thach ?? 0

  async function handlePurchase() {
    if (!selectedTier || !user) return
    setPurchasing(true)
    setError(null)
    try {
      await apiFetch("/vip/purchase", { method: "POST", body: JSON.stringify({ tier: selectedTier }) })
      setSuccess(true)
      const [subs, w] = await Promise.all([
        apiFetch<VipSubscription[]>("/vip/me"),
        apiFetch<Wallet>("/economy/wallet"),
      ])
      const active = subs.find((s: VipSubscription) => s.status === "active")
      if (active) setCurrentVip(active)
      if (w) setWallet(w)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Đã xảy ra lỗi"
      const price = selectedTier === "pro" ? proPriceLT : maxPriceLT
      setError(msg.includes("402") || msg.toLowerCase().includes("insufficient")
        ? "Không đủ Linh Thạch. Bạn cần " + formatLT(price) + " LT."
        : "Không thể mua VIP. Vui lòng thử lại.")
    } finally {
      setPurchasing(false)
    }
  }

  const proCardClass = selectedTier === "pro"
    ? "cursor-pointer rounded-xl border-2 p-6 transition-all border-amber-500 bg-amber-50/50 dark:bg-amber-900/10"
    : "cursor-pointer rounded-xl border-2 p-6 transition-all border-border hover:border-amber-300"

  const maxCardClass = selectedTier === "max"
    ? "cursor-pointer rounded-xl border-2 p-6 transition-all relative border-purple-500 bg-purple-50/50 dark:bg-purple-900/10"
    : "cursor-pointer rounded-xl border-2 p-6 transition-all relative border-border hover:border-purple-300"

  const btnLabel = purchasing
    ? "Đang xử lý..."
    : selectedTier
    ? "Mua VIP " + (selectedTier === "pro" ? "Pro" : "Max") + " — " + formatLT(selectedTier === "pro" ? proPriceLT : maxPriceLT) + " LT"
    : "Chọn gói VIP"

  if (success) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
          <span className="text-4xl">✓</span>
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold">Đăng ký VIP thành công!</h1>
          <p className="text-muted-foreground">Đặc quyền VIP đã được kích hoạt ngay lập tức.</p>
        </div>
        <div className="flex gap-4">
          <Button onClick={() => router.push("/novels")}>Đọc truyện</Button>
          <Button variant="outline" onClick={() => router.push("/")}>Về trang chủ</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 space-y-8">
      <div className="text-center space-y-2">
        <div className="flex justify-center">
          <span className="text-5xl">👑</span>
        </div>
        <h1 className="text-3xl font-bold">Nâng cấp VIP</h1>
        <p className="text-muted-foreground">Mua VIP bằng Linh Thạch để mở khoá đặc quyền đọc sớm</p>
      </div>

      {user && wallet && (
        <div className="flex items-center justify-center gap-3 rounded-lg border p-4 bg-muted/30">
          <span className="text-2xl">💎</span>
          <div>
            <div className="font-semibold">{formatLT(ltBalance)} Linh Thạch</div>
            <div className="text-sm text-muted-foreground">Số dư ví hiện tại</div>
          </div>
          <Button variant="outline" size="sm" onClick={() => router.push("/wallet/deposit")} className="ml-4">
            Nạp thêm
          </Button>
        </div>
      )}

      {currentVip && (
        <div className="rounded-lg border border-green-500/30 bg-green-50 dark:bg-green-900/10 p-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">✅</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold">Bạn đang có gói VIP</span>
                <VipBadge tier={currentVip.vip_tier} />
              </div>
              {currentVip.expires_at && (
                <div className="text-sm text-muted-foreground">
                  Hết hạn: {new Date(currentVip.expires_at).toLocaleDateString("vi-VN")}
                </div>
              )}
            </div>
          </div>
          {currentVip.vip_tier === "pro" && (
            <p className="mt-2 text-sm text-muted-foreground">
              Muốn nâng lên VIP Max? Vui lòng{" "}
              <a href="/feedbacks" className="underline">liên hệ admin</a> để được hỗ trợ.
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div onClick={() => setSelectedTier("pro")} className={proCardClass}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold">VIP Pro</h2>
              <VipBadge tier="pro" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{formatLT(proPriceLT)}</div>
              <div className="text-sm text-muted-foreground">Linh Thạch / 30 ngày</div>
            </div>
          </div>
          <ul className="space-y-2">
            {PRO_FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                {f}
              </li>
            ))}
          </ul>
          {ltBalance < proPriceLT && user && (
            <p className="mt-3 text-xs text-red-500">Cần thêm {formatLT(proPriceLT - ltBalance)} LT</p>
          )}
        </div>

        <div onClick={() => setSelectedTier("max")} className={maxCardClass}>
          <div className="absolute -top-3 right-4">
            <span className="rounded-full bg-purple-600 px-3 py-0.5 text-xs font-semibold text-white">
              Phổ biến nhất
            </span>
          </div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold">VIP Max</h2>
              <VipBadge tier="max" />
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{formatLT(maxPriceLT)}</div>
              <div className="text-sm text-muted-foreground">Linh Thạch / 30 ngày</div>
            </div>
          </div>
          <ul className="space-y-2">
            {MAX_FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm">
                <span className="text-green-500">✓</span>
                {f}
              </li>
            ))}
          </ul>
          {ltBalance < maxPriceLT && user && (
            <p className="mt-3 text-xs text-red-500">Cần thêm {formatLT(maxPriceLT - ltBalance)} LT</p>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/10 border border-red-200 p-4 text-sm text-red-700 dark:text-red-400">
          {error}
          {error.includes("Linh Thạch") && (
            <Button variant="link" size="sm" onClick={() => router.push("/wallet/deposit")} className="ml-2 text-red-600 p-0">
              Nạp ngay →
            </Button>
          )}
        </div>
      )}

      {!user ? (
        <div className="text-center">
          <p className="text-muted-foreground mb-3">Bạn cần đăng nhập để mua VIP</p>
          <Button onClick={() => router.push("/auth/login")}>Đăng nhập</Button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <Button
            size="lg"
            onClick={handlePurchase}
            disabled={!selectedTier || purchasing}
            className="w-full max-w-xs"
          >
            {btnLabel}
          </Button>
          <p className="text-xs text-muted-foreground text-center">
            Giao dịch không hoàn tiền. Thời hạn 30 ngày kể từ khi mua.
          </p>
        </div>
      )}
    </div>
  )
}
