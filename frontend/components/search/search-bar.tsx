"use client";

import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface SearchBarProps {
  defaultValue?: string;
  className?: string;
}

export function SearchBar({ defaultValue = "", className }: SearchBarProps) {
  const router = useRouter();

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const q = new FormData(e.currentTarget).get("q") as string;
    router.push(`/novels?q=${encodeURIComponent(q.trim())}`);
  }

  return (
    <form onSubmit={handleSubmit} className={`flex gap-2 ${className ?? ""}`}>
      <Input
        name="q"
        defaultValue={defaultValue}
        placeholder="Tìm kiếm truyện..."
        className="h-8 w-40 md:w-56 lg:w-72"
      />
      <Button type="submit" size="sm" variant="ghost" className="h-8 px-2">
        <Search className="h-4 w-4" />
        <span className="sr-only">Tìm kiếm</span>
      </Button>
    </form>
  );
}
