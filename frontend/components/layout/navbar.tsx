"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useUser } from "@/lib/hooks/use-user"
import { apiFetch } from "@/lib/api"
import { UserMenu } from "@/components/auth/user-menu"
import { SearchBar } from "@/components/search/search-bar"
import { WalletBadge } from "@/components/economy/wallet-badge"
import { NotificationBell } from "@/components/notifications/notification-bell"
import type { Wallet } from "@/lib/types/economy"

export function Navbar() {
  const { user } = useUser()
  const [wallet, setWallet] = useState<Wallet | null>(null)

  useEffect(() => {
    if (!user) return
    apiFetch<Wallet>("/economy/wallet").then(setWallet).catch(() => null)
  }, [user])

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-14 items-center justify-between gap-4 px-4">
        <Link href="/" className="shrink-0 text-xl font-bold tracking-tight">
          NovelVerse
        </Link>

        <nav className="hidden items-center gap-6 text-sm md:flex">
          <Link
            href="/novels"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Truyện
          </Link>
          <Link
            href="/leaderboard"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Bảng xếp hạng
          </Link>
          <Link
            href="/library"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Thư viện
          </Link>
          {user && (
            <Link
              href="/wallet"
              className="flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground"
            >
              Ví
              {wallet && <WalletBadge balance={wallet.linh_thach} />}
            </Link>
          )}
        </nav>

        <div className="flex flex-1 items-center justify-end gap-3">
          <SearchBar />
          <NotificationBell />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
