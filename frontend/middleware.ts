import { auth } from "./auth";

// MatchPulse public exploration middleware
// Allows viewers and judges to explore the live dashboard and 2D radar seamlessly,
// while preserving NextAuth session capabilities for authenticated routes.
export default auth((req) => {
  // Let all visitors through to explore the platform
  return;
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};

