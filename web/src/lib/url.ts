// The page address holds the reader's choices, so a shared link opens on the same answer.

import { PLACE_MAX, PLACE_MIN, type Sex } from "./degree";

export interface Choice {
  subject: string | null;
  sex: Sex;
  place: number;
  uni: number | null;
}

const SEX_CODE: Record<Sex, string> = { Total: "all", Female: "women", Male: "men" };

export function readChoice(search: string): Choice {
  const q = new URLSearchParams(search);
  const sex = (Object.keys(SEX_CODE) as Sex[]).find((k) => SEX_CODE[k] === q.get("g")) ?? "Total";
  const p = Number(q.get("p"));
  const u = Number(q.get("u"));
  return {
    subject: q.get("s"),
    sex,
    place: Number.isInteger(p) && p >= PLACE_MIN && p <= PLACE_MAX ? p : 50,
    uni: q.has("u") && Number.isInteger(u) && u >= 0 ? u : null,
  };
}

export function writeChoice(c: Choice): string {
  const q = new URLSearchParams();
  if (c.subject) q.set("s", c.subject);
  if (c.sex !== "Total") q.set("g", SEX_CODE[c.sex]);
  if (c.place !== 50) q.set("p", String(c.place));
  if (c.uni !== null) q.set("u", String(c.uni));
  const s = q.toString();
  return s ? `?${s}` : "";
}
