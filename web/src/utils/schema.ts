import { z } from "astro/zod";

export const paperRecordSchema = z.object({
  date: z.string(),
  title: z.string(),
  authors: z.array(z.string()),
  url: z.string(),
  code: z.string().nullable(),
  model: z.string().nullable().optional(),
  abstract: z.string().optional(),
  categories: z.array(z.string()),
});

export const paperValueSchema = z.union([z.string(), paperRecordSchema]);
export const paperBucketSchema = z.record(z.string(), z.record(z.string(), paperValueSchema));
