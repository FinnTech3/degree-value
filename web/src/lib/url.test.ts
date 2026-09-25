import { describe, expect, it } from "vitest";
import { readChoice, writeChoice } from "./url";

describe("page address", () => {
  it("round-trips a full choice", () => {
    const c = { subject: "economics", sex: "Female" as const, place: 70, uni: 12 };
    expect(readChoice(writeChoice(c))).toEqual(c);
  });

  it("keeps the address empty for the defaults", () => {
    expect(writeChoice({ subject: null, sex: "Total", place: 50, uni: null })).toBe("");
  });

  it("ignores places outside the slider and nonsense", () => {
    expect(readChoice("?p=200").place).toBe(50);
    expect(readChoice("?p=abc&g=x&u=-3")).toEqual({ subject: null, sex: "Total", place: 50, uni: null });
  });
});
