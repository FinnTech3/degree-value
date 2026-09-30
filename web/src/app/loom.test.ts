// What the loom draws, held to the subjects the pipeline wrote off. The count
// has been wrong once: a thread runs to the edge when the loan is written off,
// which is not the same as repaying for the full forty years. English studies
// repays all forty and clears in the last of them.

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { DegreeFile } from "../lib/degree";
import { order, owedAt } from "./Loom";

const d = JSON.parse(readFileSync("public/data/degree.json", "utf8")) as DegreeFile;
const rows = order(d.subjects, d.balance_real);

describe("the loom", () => {
  it("draws every subject once, quickest to clear first", () => {
    expect(rows).toHaveLength(d.subjects.length);
    expect(new Set(rows.map((r) => r.s.name)).size).toBe(d.subjects.length);
    for (let i = 1; i < rows.length; i++) expect(rows[i]!.s.years).toBeGreaterThanOrEqual(rows[i - 1]!.s.years);
    expect(rows[0]!.s.cleared).toBe(true);
  });

  it("runs exactly the written-off threads off the edge", () => {
    const off = rows.filter((r) => !r.s.cleared).map((r) => r.s.name);
    expect(off.sort()).toEqual([...d.written_off].sort());
    expect(off).toHaveLength(9);
    // repaying for the full term is not the same as being written off
    expect(rows.filter((r) => r.s.years >= d.term)).toHaveLength(10);
    const full = rows.find((r) => r.s.years >= d.term && r.s.cleared)!;
    expect(full.s.name).toBe("English studies");
    expect(owedAt(full, d.term)).toBeNull();
  });

  it("thickens a thread by what is still owed, and ends it where the loan does", () => {
    for (const r of rows) {
      expect(r.owed[0]).toBe(d.balance_real);
      expect(owedAt(r, 0)).toBe(d.balance_real);
      // still owed in the year before it clears, nothing from that year on
      if (r.s.cleared) {
        expect(owedAt(r, r.s.years - 1)).toBeGreaterThan(0);
        expect(owedAt(r, r.s.years)).toBeNull();
      } else {
        expect(owedAt(r, d.term)).toBeGreaterThan(0);
      }
    }
  });

  it("accounts for all 34 subjects at every age it can be scrubbed to", () => {
    for (let years = 0; years <= d.term; years++) {
      const done = rows.filter((r) => owedAt(r, years) === null && r.s.cleared).length;
      const owing = rows.filter((r) => owedAt(r, years) !== null).length;
      expect(done + owing).toBe(rows.length);
    }
    // and at the end of the term it is the written-off nine still owing
    expect(rows.filter((r) => owedAt(r, d.term) !== null)).toHaveLength(9);
  });
});
