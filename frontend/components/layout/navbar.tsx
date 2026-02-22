import Link from "next/link";
import { UserMenu } from "@/components/auth/user-menu";
import { SearchBar } from "@/components/search/search-bar";

export function Navbar() {
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
            href="/rankings"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Bảng xếp hạng
          </Link>
        </nav>

        <div className="flex flex-1 items-center justify-end gap-3">
          <SearchBar />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
