import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/unauthorized(.*)",
]);

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default publishableKey
  ? clerkMiddleware(
      async (auth, request) => {
        if (!isPublicRoute(request)) {
          await auth.protect();
        }
      },
      {
        signInUrl: "/sign-in",
        signUpUrl: "/sign-up",
      }
    )
  : (_request: NextRequest) => NextResponse.next();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};

