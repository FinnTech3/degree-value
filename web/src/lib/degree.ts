// The app's reading of data/built/degree.json. Every loan outcome in it was
// worked out by pipeline/src/degreevalue/loans.py; this only looks them up.

export type Sex = "Total" | "Female" | "Male";

export interface Places {
  years: number[];
  cleared: boolean[];
  repaid: number[];
}

export interface Subject {
  name: string;
  /** What the median graduate still owes at the end of each year, £ at 2024-25 prices, until cleared or written off. */
  thread: number[];
  graduates: number;
  full: number;
  years: number;
  /** Whether the median graduate clears the loan before it is written off. */
  cleared: boolean;
  repaid: number;
  full_moving: number;
  years_moving: number;
  rank1: number | null;
  rank10: number | null;
  paths: Record<Sex, Record<string, [number | null, number | null, number | null]>>;
  places: Partial<Record<Sex, Places>>;
  /** Share not in sustained work or study five years out: the lowest places, given no earnings. */
  not_working: Partial<Record<Sex, number>>;
  /** [provider index, median 1, 3 and 5 years out, graduates in the 5-year figure] */
  universities: [number, number | null, number | null, number | null, number | null][];
}

export interface DegreeFile {
  places: number[];
  first_year: number;
  graduation_age: number;
  term: number;
  balance: number;
  /** The balance when repayments begin, at 2024-25 prices. */
  balance_real: number;
  growth: number;
  model: Summary;
  dfe: Summary;
  written_off: string[];
  written_off_share: number;
  checks: { name: string; passed: boolean; summary: string }[];
  providers: [name: string, type: string][];
  subjects: Subject[];
}

export interface Summary {
  full_repayment_share: number;
  median_years: number;
  repayments_real: number;
  share_repaid_real: number;
}

export interface Outcome {
  years: number;
  cleared: boolean;
  repaid: number;
  /** The age at the end of the last year of repayment. */
  age: number;
  /** The tax year the loan is cleared or written off in, e.g. "2042-43". */
  taxYear: string;
}

export const PLACE_MIN = 5;
export const PLACE_MAX = 95;

export function clampPlace(p: number): number {
  return Math.min(PLACE_MAX, Math.max(PLACE_MIN, Math.round(p)));
}

export function taxYear(start: number): string {
  return `${start}-${String((start + 1) % 100).padStart(2, "0")}`;
}

/** The loan of a graduate at `place` (5 to 95) among their subject's graduates. */
export function outcome(d: DegreeFile, s: Subject, sex: Sex, place: number): Outcome | null {
  const p = s.places[sex];
  if (!p) return null;
  const i = d.places.findIndex((q) => Math.round(q * 100) === clampPlace(place));
  if (i < 0) return null;
  const years = p.years[i]!;
  return {
    years,
    cleared: p.cleared[i]!,
    repaid: p.repaid[i]!,
    age: d.graduation_age + years,
    taxYear: taxYear(d.first_year + years - 1),
  };
}

/** The lowest place at which the loan is cleared before it is written off, or null if nobody clears it. */
export function clearingPlace(d: DegreeFile, s: Subject, sex: Sex): number | null {
  const p = s.places[sex];
  if (!p) return null;
  const i = p.cleared.findIndex((c) => c);
  return i < 0 ? null : Math.round(d.places[i]! * 100);
}

export interface University {
  name: string;
  type: string;
  y1: number | null;
  y3: number | null;
  y5: number | null;
  n5: number | null;
}

export function universities(d: DegreeFile, s: Subject): University[] {
  return s.universities.map(([i, y1, y3, y5, n5]) => {
    const [name, type] = d.providers[i]!;
    return { name, type, y1, y3, y5, n5 };
  });
}

/** Share of the subject's universities with a published 5-year median below `pay`. */
export function shareBelow(unis: University[], pay: number): number {
  const known = unis.filter((u) => u.y5 !== null);
  return known.length ? known.filter((u) => u.y5! < pay).length / known.length : 0;
}

export function slug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
