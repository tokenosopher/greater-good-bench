import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Loaded by art-crit, after openrouter_routing.ts, for unpinned `openrouter/google/*` runs (Gemini).
//
// Why: Gemini signs its reasoning ("thought signature", returned as an encrypted `reasoning_details`
// entry). pi 1.4.0 already stores that entry and sends it back verbatim on the assistant message, as
// OpenRouter asks. But OpenRouter may serve the next request of the same agent loop from another
// upstream (Google Vertex -> Google AI Studio after a 429), which can't verify the other one's
// signature: Google answers "Corrupted thought signature" and OpenRouter reports it as
// "Gemini models require OpenRouter reasoning details to be preserved in each request" (400).
//
// Fix: once the first response names its upstream (the stream's `provider`, a display name), every
// later request of this pi process is pinned to that upstream (`provider.only` + no fallbacks).
// A run pinned with `MODEL@slug` (ART_CRIT_OPENROUTER_ROUTING) is already sticky: nothing to do.
// An upstream name missing from UPSTREAM_SLUGS is left unpinned (OpenRouter wants slugs, not names).

export const UPSTREAM_SLUGS: Record<string, string> = {
  Google: "google-vertex",
  "Google AI Studio": "google-ai-studio",
};

/** The request body pinned to `slug`, or unchanged when there's no slug or the body already chose upstreams. */
export function pinUpstream(body: Record<string, unknown>, slug: string | null): Record<string, unknown> {
  const provider = (body.provider as Record<string, unknown> | undefined) ?? {};
  if (!slug || provider.only || provider.order) return body;
  return { ...body, provider: { ...provider, only: [slug], allow_fallbacks: false } };
}

export default function (pi: ExtensionAPI) {
  if (process.env.ART_CRIT_OPENROUTER_ROUTING) return;
  let named = false; // the first named upstream decides, even when it has no known slug
  let slug: string | null = null;
  pi.on("provider_stream_event", (event) => {
    const name = (event.data as { provider?: unknown } | null)?.provider;
    if (named || typeof name !== "string") return;
    named = true;
    slug = UPSTREAM_SLUGS[name] ?? null;
  });
  pi.on("before_provider_request", (event) => pinUpstream(event.payload as Record<string, unknown>, slug));
}
