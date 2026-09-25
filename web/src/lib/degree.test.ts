// The app's lookups against the numbers the README quotes.

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { type DegreeFile, clearingPlace, outcome, shareBelow, slug, taxYear, universities } from "./degree";

const d = JSON.parse(readFileSync("public/data/degree.json", "utf8")) as DegreeFile;
const bySubject = (n: string) => d.subjects.find((s) => s.name === n)!;

describe("the data", () => {
  it("holds the 34 subjects the loan model covers, every one with a slider for all three groups", () => {
    expect(d.subjects).toHaveLength(34);
    for (const s of d.subjects)
      for (const sex of ["Total", "Female", "Male"] as const) expect(s.places[sex]).toBeTruthy();
  });

  it("says what the README says", () => {
    expect(d.written_off).toHaveLength(10);
    expect(Math.round(d.written_off_share * 100)).toBe(34);
    expect(bySubject("Economics").years).toBe(15);
    expect(bySubject("Medicine and dentistry").years).toBe(14);
    expect(bySubject("Performing arts").years).toBe(40);
    expect(Math.round(d.model.full_repayment_share * 100)).toBe(56);
    expect(d.checks.every((c) => c.passed)).toBe(true);
  });

  it("gives every subject's slugs once", () => {
    const slugs = d.subjects.map((s) => slug(s.name));
    expect(new Set(slugs).size).toBe(slugs.length);
  });
});

describe("a reader's loan", () => {
  it("ends in the right tax year and at the right age", () => {
    const o = outcome(d, bySubject("Economics"), "Total", 50)!;
    expect(o.age).toBe(d.graduation_age + o.years);
    expect(o.taxYear).toBe(taxYear(d.first_year + o.years - 1));
    expect(taxYear(2042)).toBe("2042-43");
    expect(taxYear(2099)).toBe("2099-00");
  });

  it("is written off at forty years for anyone who never clears it", () => {
    const s = bySubject("Performing arts");
    const low = outcome(d, s, "Total", 10)!;
    expect(low.cleared).toBe(false);
    expect(low.years).toBe(40);
    expect(low.age).toBe(61);
  });

  it("clamps places to the slider's range", () => {
    const s = bySubject("Law");
    expect(outcome(d, s, "Total", 1)).toEqual(outcome(d, s, "Total", 5));
    expect(outcome(d, s, "Total", 99)).toEqual(outcome(d, s, "Total", 95));
  });

  it("finds where a subject's graduates start clearing their loans", () => {
    const s = bySubject("Law");
    const q = clearingPlace(d, s, "Total")!;
    expect(outcome(d, s, "Total", q)!.cleared).toBe(true);
    expect(outcome(d, s, "Total", q - 1)!.cleared).toBe(false);
  });
});

describe("universities", () => {
  it("finds a real published figure: Oxford Brookes economics, five years out", () => {
    const u = universities(d, bySubject("Economics")).find((x) => x.name.includes("Brookes"))!;
    expect(u.y5).toBe(46_400);
    expect(u.n5).toBe(40);
  });

  it("ranks a figure among the subject's universities", () => {
    const unis = universities(d, bySubject("Economics"));
    expect(shareBelow(unis, 0)).toBe(0);
    expect(shareBelow(unis, 1e9)).toBe(1);
  });
});
