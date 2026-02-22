"use client";
import { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  value: number;        // current rating (0-5)
  onChange?: (v: number) => void; // if provided, interactive
  size?: "sm" | "md" | "lg";
}

export function StarRating({ value, onChange, size = "md" }: StarRatingProps) {
  const [hovered, setHovered] = useState(0);
  const active = hovered || value;
  const sizes = { sm: 14, md: 18, lg: 24 };
  const px = sizes[size];

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          width={px}
          height={px}
          className={cn(
            "transition-colors",
            active >= star ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground",
            onChange && "cursor-pointer hover:text-yellow-400"
          )}
          onClick={() => onChange?.(star)}
          onMouseEnter={() => onChange && setHovered(star)}
          onMouseLeave={() => onChange && setHovered(0)}
        />
      ))}
    </div>
  );
}
