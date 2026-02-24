"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export function WelcomeLoginButton() {
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setLoading(true);
    const supabase = createClient();
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  }

  return (
    <Button
      onClick={handleLogin}
      disabled={loading}
      size="lg"
      className="h-14 px-8 text-base w-full sm:w-auto rounded-full shadow-lg hover:shadow-primary/25 transition-all"
    >
      {loading ? "Đang chuyển hướng..." : "Đăng nhập & Đọc ngay"}
    </Button>
  );
}
