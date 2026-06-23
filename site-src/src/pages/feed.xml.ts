import rss from "@astrojs/rss";
import { getCollection } from "astro:content";

export async function GET(context) {
  const posts = (await getCollection("blog", (p) => !p.data.draft))
    .sort((a, b) => +new Date(b.data.date ?? 0) - +new Date(a.data.date ?? 0));
  return rss({
    title: "The Luya Blog",
    description: "Microgreens nutrition, health, recipes, and home growing — by Luya.",
    site: context.site,
    items: posts.map((p) => ({
      title: p.data.title,
      description: p.data.description,
      pubDate: p.data.date ? new Date(p.data.date) : new Date(),
      link: `/${p.slug}/`,
    })),
  });
}
