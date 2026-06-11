import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/dashboard", "/company"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p));

  if (isProtected) {
    // Token lives in localStorage (client-only) so we can't read it here.
    // Actual protection is enforced by the AuthGuard component on each page.
    // For SSR-safe protection, migrate to cookie-based sessions later.
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/company/:path*"],
};
