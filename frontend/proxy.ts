import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

export async function proxy(request: NextRequest) {
  const response = NextResponse.next({
    request,
  });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // IMPORTANT: This refreshes the session
  const {
    data: { user },
  } = await supabase.auth.getUser();

  // Routing Logic
  // If the user is at "/" and is NOT logged in -> redirect to "/welcome"
  if (!user && request.nextUrl.pathname === "/") {
    return NextResponse.redirect(new URL("/welcome", request.url));
  }

  // If the user is at "/welcome" and IS logged in -> redirect to "/"
  if (user && request.nextUrl.pathname === "/welcome") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
