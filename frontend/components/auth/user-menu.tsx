"use client";

import { createClient } from "@/lib/supabase/client";
import { useUser } from "@/lib/hooks/use-user";
import { useEffect, useState } from "react";
import { LoginButton } from "@/components/auth/login-button";
import { VipBadge } from "@/components/vip/vip-badge";
import { WalletBadge } from "@/components/economy/wallet-badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { apiFetch } from "@/lib/api";
import type { VipSubscription } from "@/lib/types/vip";
import type { Wallet } from "@/lib/types/economy";

export function UserMenu() {
  const { user, loading } = useUser();
  const [vipTier, setVipTier] = useState<"pro" | "max" | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);

  useEffect(() => {
    if (!user) return;
    apiFetch<VipSubscription | null>("/vip/me")
      .then((data) => {
        if (
          data?.status === "active" &&
          data?.expires_at &&
          new Date(data.expires_at) > new Date()
        ) {
          setVipTier(data.vip_tier);
        }
      })
      .catch(() => {});

    apiFetch<Wallet>("/economy/wallet")
      .then(setWallet)
      .catch(() => null);
  }, [user]);

  if (loading) {
    return <div className="h-9 w-24 animate-pulse rounded-md bg-muted" />;
  }

  if (!user) {
    return <LoginButton />;
  }

  const avatarUrl = user.user_metadata?.avatar_url as string | undefined;
  const fullName = user.user_metadata?.full_name as string | undefined;

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    window.location.href = "/";
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center gap-2 px-2">
          {avatarUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={avatarUrl}
              alt={fullName ?? "User"}
              className="h-7 w-7 rounded-full object-cover"
            />
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
              {(fullName ?? "U")[0].toUpperCase()}
            </div>
          )}
          <span className="max-w-[120px] truncate text-sm">
            {fullName ?? user.email}
          </span>
          {vipTier && <VipBadge tier={vipTier} />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="truncate text-xs text-muted-foreground">
          {user.email}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a href="/profile">Hồ sơ</a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a
            href="/wallet"
            className="flex w-full items-center justify-between"
          >
            <span>Ví</span>
            {wallet && <WalletBadge balance={wallet.linh_thach} />}
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href="/vip">Đăng ký VIP</a>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout} className="text-destructive">
          Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
