import { SITE_NAME } from "../config.ts";
import type { APIContext } from "astro";
import { MAIN_FEED_LIMIT, buildFeedItems, feedResponse } from "../utils/feed.ts";
import { resolveLatest } from "../utils/papers.ts";
export async function GET(context: APIContext) {
  const { keywords } = resolveLatest();
  return feedResponse(context, {
    title: SITE_NAME,
    description: "Updated every two days: AI infra arxiv paper digest",
    items: buildFeedItems(keywords, MAIN_FEED_LIMIT),
  });
}
