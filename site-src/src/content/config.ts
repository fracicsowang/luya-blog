// Blog post schema. Drafts live in /blog-drafts/ and are copied into
// src/content/ at publish time by blog-tools/ci_publish.py.
// Schema is tolerant: `date` is set by the publisher; extra fields are allowed.
import { defineCollection, z } from "astro:content";

const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string().max(200),
    description: z.string().max(500),
    primary_keyword: z.string(),
    category: z.string().default("Microgreens"),
    audience: z.string().optional(),
    author: z.string().default("Luya Editorial"),
    author_role: z.string().optional(),
    read_time: z.string().optional(),
    date: z.coerce.date().optional(),
    image: z.string().optional(),        // hero / OG image (absolute path under /blog)
    image_alt: z.string().optional(),
    hero_image: z.string().optional(),
    hero_image_prompt: z.string().optional(),
    medical_disclaimer: z.boolean().default(false),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
