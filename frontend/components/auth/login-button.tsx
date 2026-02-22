"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export function LoginButton() {
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
    // Page will redirect; no need to setLoading(false)
  }

  return (
    <Button onClick={handleLogin} disabled={loading} variant="outline">
      {loading ? "Redirecting..." : "Sign in with Google"}
    </Button>
  );
}
