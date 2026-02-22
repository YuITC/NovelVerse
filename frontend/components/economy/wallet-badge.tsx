"use client"

import { cn } from "@/lib/utils"

interface WalletBadgeProps {
  balance: number;
  className?: string;
}

function formatBalance(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}tr`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
  return n.toFixed(0)
}

export function WalletBadge({ balance, className }: WalletBadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
      className
    )}>
      <span>💎</span>
      <span>{formatBalance(balance)}</span>
    </span>
  )
}
