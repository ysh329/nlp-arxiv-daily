export interface PaperRecord { date: string; title: string; authors: string[]; url: string; code: string | null; abstract?: string; categories: string[]; }
export type PaperValue = string | PaperRecord;
export interface ParsedPaper { date: string; title: string; firstAuthor: string; authors: string[]; paperUrl: string; codeLink: string | null; abstract: string | null; categories: string[]; }
export function parsePaper(value: PaperValue): ParsedPaper | null {
  if (typeof value === "string") return parsePaperRow(value);
  if (!value.title || !value.date || !value.url) return null;
  const authors = value.authors ?? [];
  return { date: value.date, title: value.title, firstAuthor: authors[0] ?? "", authors, paperUrl: value.url, codeLink: value.code ?? null, abstract: value.abstract || null, categories: value.categories ?? [] };
}
const BULLET_RE = /^-\s+(\d{4}-\d{2}-\d{2}),\s+\*\*(.+?)\*\*,\s+(.+?)\s+et\.al\.,\s+Paper:\s+\[(.+?)\]\(.+?\)(?:,\s+Code:\s+\*\*\[(.+?)\]\(.+?\)\*\*)?\s*$/;
const PIPE_RE = /^\|\*\*(\d{4}-\d{2}-\d{2})\*\*\|\*\*(.+?)\*\*\|(.+?)\s+et\.al\.\|\[.+?\]\((.+?)\)\|(.+?)\|\s*$/;
export function parsePaperRow(row: string): ParsedPaper | null {
  const trimmed = row.trim();
  const bullet = trimmed.match(BULLET_RE);
  if (bullet) { const [, date, title, firstAuthor, paperUrl, codeLink] = bullet; return { date, title, firstAuthor, authors: [], paperUrl, codeLink: codeLink ?? null, abstract: null, categories: [] }; }
  const pipe = trimmed.match(PIPE_RE);
  if (pipe) { const [, date, title, firstAuthor, paperUrl, codeCell] = pipe; const codeMatch = codeCell.match(/\*\*\[.+?\]\((.+?)\)\*\*/); return { date, title, firstAuthor, authors: [], paperUrl, codeLink: codeMatch ? codeMatch[1] : null, abstract: null, categories: [] }; }
  return null;
}
export function sortPapersDesc(papers: Record<string, PaperValue>): Array<[string, PaperValue]> {
  return Object.entries(papers).sort(([a, rowA], [b, rowB]) => {
    const surveyA = parsePaper(rowA)?.title.match(/\b(survey|review|overview)\b/i) ? 1 : 0;
    const surveyB = parsePaper(rowB)?.title.match(/\b(survey|review|overview)\b/i) ? 1 : 0;
    if (surveyA !== surveyB) return surveyB - surveyA;
    return a < b ? 1 : a > b ? -1 : 0;
  });
}
