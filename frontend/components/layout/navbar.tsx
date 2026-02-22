import Link from "next/link";
import { UserMenu } from "@/components/auth/user-menu";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-14 items-center justify-between px-4">
        <Link href="/" className="text-xl font-bold tracking-tight">
          NovelVerse
        </Link>

        <nav className="hidden items-center gap-6 text-sm md:flex">
          <Link href="/novels" className="text-muted-foreground transition-colors hover:text-foreground">
            Browse
          </Link>
          <Link href="/rankings" className="text-muted-foreground transition-colors hover:text-foreground">
            Rankings
          </Link>
        </nav>

        <UserMenu />
      </div>
    </header>
  );
}
