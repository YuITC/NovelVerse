import { cn } from "@/lib/utils";

interface VipBadgeProps {
  tier: "pro" | "max" | "none" | null | undefined;
  className?: string;
}

export function VipBadge({ tier, className }: VipBadgeProps) {
  if (!tier || tier === "none") return null;

  if (tier === "pro") {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
          "bg-amber-100 text-amber-800 border border-amber-300",
          "dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700",
          className
        )}
      >
        VIP Pro
      </span>
    );
  }

  if (tier === "max") {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
          "bg-purple-100 text-purple-800 border border-purple-300",
          "dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-700",
          className
        )}
      >
        VIP Max
      </span>
    );
  }

  return null;
}
