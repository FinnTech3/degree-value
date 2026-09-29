// The result as a 1080 by 1350 picture, the shape that fills a phone screen in
// a feed: the years, the subject, and the loom in miniature with the reader's
// thread picked out. Drawn in the browser; nothing is uploaded anywhere.

import type { Subject } from "../lib/degree";
import { order } from "./Loom";

export interface CardContent {
  years: number;
  cleared: boolean;
  age: number;
  subject: string;
  place: number;
  lines: string[];
  subjects: Subject[];
  /** The balance when repayments begin, at 2024-25 prices: where every thread starts. */
  start: number;
  graduationAge: number;
  term: number;
}

export const CARD_W = 1080;
export const CARD_H = 1350;

// The page's light theme, fixed, so the picture looks the same whoever saves it.
const PAPER = "#f4efe4";
const INK = "#16203f";
const INK_2 = "#3b4566";
const MUTED = "#586079";
const RULE = "#d9d0bd";
const NAVY = "#1b2a5c";
const THREAD = "#1b2a5c";
const THREAD_OFF = "#7a83a6";
const FOIL = ["#c2378a", "#6a4fd6", "#1f7fa0"];

const FONTS = [
  '700 250px "IBM Plex Sans Condensed"',
  '600 56px "IBM Plex Serif"',
  'italic 600 56px "IBM Plex Serif"',
  '400 36px "IBM Plex Sans"',
  '400 26px "IBM Plex Mono"',
];

export async function fontsReady(): Promise<void> {
  try {
    await Promise.all(FONTS.map((f) => document.fonts.load(f)));
  } catch {
    // The card still draws in the fallback fonts.
  }
}

function wrap(ctx: CanvasRenderingContext2D, text: string, width: number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of text.split(" ")) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width > width && line) {
      lines.push(line);
      line = word;
    } else line = next;
  }
  if (line) lines.push(line);
  return lines;
}

/** Every subject's thread, fitted into a box, with the reader's own in foil. */
function loom(ctx: CanvasRenderingContext2D, c: CardContent, x0: number, y0: number, w: number, h: number) {
  const rows = order(c.subjects, c.start);
  const rowH = h / rows.length;
  const maxOwed = Math.max(...rows.flatMap((r) => r.owed));
  const x = (k: number) => x0 + (k / c.term) * w;
  const cy = (i: number) => y0 + i * rowH + rowH / 2;
  const middle = y0 + h / 2;
  const FAN = 5;
  const lane = (i: number, k: number) => {
    const t = Math.min(1, k / FAN);
    return middle + (cy(i) - middle) * (t * t * (3 - 2 * t));
  };
  const thick = (b: number) => Math.max(1, (b / maxOwed) * rowH * 0.62);

  rows.forEach((r, i) => {
    const mine = r.s.name === c.subject;
    if (mine) {
      const g = ctx.createLinearGradient(x0, 0, x0 + w, 0);
      FOIL.forEach((colour, k) => g.addColorStop(k / (FOIL.length - 1), colour));
      ctx.fillStyle = g;
    } else ctx.fillStyle = r.s.cleared ? THREAD : THREAD_OFF;
    ctx.globalAlpha = mine ? 1 : 0.8;
    ctx.beginPath();
    r.owed.forEach((b, k) => {
      const px = x(k);
      const py = lane(i, k) - (b > 0 ? thick(b) / 2 : 0);
      if (k === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    for (let k = r.owed.length - 1; k >= 0; k--) {
      ctx.lineTo(x(k), lane(i, k) + (r.owed[k]! > 0 ? thick(r.owed[k]!) / 2 : 0));
    }
    ctx.closePath();
    ctx.fill();
    // a knot where it is cleared, a frayed end where it is not
    const last = r.owed.length - 1;
    if (r.s.cleared) {
      ctx.beginPath();
      ctx.arc(x(last), cy(i), mine ? 8 : 4, 0, 2 * Math.PI);
      ctx.fill();
    }
  });
  ctx.globalAlpha = 1;
}

export function drawCard(canvas: HTMLCanvasElement, c: CardContent): void {
  canvas.width = CARD_W;
  canvas.height = CARD_H;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const P = 84;
  const inner = CARD_W - 2 * P;
  ctx.textBaseline = "alphabetic";
  ctx.textAlign = "left";

  ctx.fillStyle = PAPER;
  ctx.fillRect(0, 0, CARD_W, CARD_H);

  // the seal and the series line
  ctx.strokeStyle = INK;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(P + 34, P + 34, 34, 0, 2 * Math.PI);
  ctx.stroke();
  ctx.fillStyle = INK;
  ctx.textAlign = "center";
  ctx.font = 'italic 600 28px "IBM Plex Serif", serif';
  ctx.fillText("FL", P + 34, P + 44);
  ctx.textAlign = "left";
  ctx.fillStyle = MUTED;
  ctx.font = '400 24px "IBM Plex Mono", monospace';
  ctx.fillText("FINN LAKIN · NO. 2 OF 6", P + 90, P + 30);
  ctx.fillText("STUDENT LOANS", P + 90, P + 62);

  let y = P + 190;
  ctx.fillStyle = INK_2;
  ctx.font = '400 36px "IBM Plex Sans", sans-serif';
  const who = c.place === 50 ? `the median ${c.subject} graduate` : `a ${c.subject} graduate at ${c.place} in 100`;
  for (const line of wrap(ctx, `A Plan 5 student loan, for ${who}`, inner)) {
    ctx.fillText(line, P, y);
    y += 46;
  }

  // the years, as large as fits beside the word
  ctx.fillStyle = NAVY;
  let size = 260;
  const measure = () => {
    ctx.font = `700 ${size}px "IBM Plex Sans Condensed", sans-serif`;
    const n = ctx.measureText(String(c.years)).width;
    ctx.font = `700 ${Math.round(size / 3)}px "IBM Plex Sans Condensed", sans-serif`;
    return n + 24 + ctx.measureText("years").width;
  };
  while (measure() > inner && size > 120) size -= 10;
  const base = y + size * 0.8;
  ctx.font = `700 ${size}px "IBM Plex Sans Condensed", sans-serif`;
  ctx.fillText(String(c.years), P - 6, base);
  const numWidth = ctx.measureText(String(c.years)).width;
  ctx.font = `700 ${Math.round(size / 3)}px "IBM Plex Sans Condensed", sans-serif`;
  ctx.fillText("years", P + numWidth + 18, base);
  y = base + 70;

  ctx.fillStyle = INK;
  ctx.font = '600 52px "IBM Plex Serif", serif';
  ctx.fillText(c.cleared ? `cleared at ${c.age}` : `written off at ${c.age}`, P, y);
  y += 56;

  ctx.fillStyle = INK_2;
  ctx.font = '400 34px "IBM Plex Sans", sans-serif';
  for (const text of c.lines) {
    for (const line of wrap(ctx, text, inner)) {
      ctx.fillText(line, P, y);
      y += 44;
    }
    y += 10;
  }

  ctx.strokeStyle = RULE;
  ctx.lineWidth = 2;
  ctx.setLineDash([2, 10]);
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(P, y);
  ctx.lineTo(CARD_W - P, y);
  ctx.stroke();
  ctx.setLineDash([]);
  y += 30;

  // every subject's thread, from 21 to 61
  const loomH = CARD_H - P - 90 - y;
  loom(ctx, c, P, y, inner, loomH);
  ctx.fillStyle = MUTED;
  ctx.font = '400 24px "IBM Plex Mono", monospace';
  ctx.fillText(String(c.graduationAge), P, y + loomH + 34);
  ctx.textAlign = "right";
  ctx.fillText(String(c.graduationAge + c.term), CARD_W - P, y + loomH + 34);
  ctx.textAlign = "left";

  ctx.fillStyle = MUTED;
  ctx.font = '400 26px "IBM Plex Mono", monospace';
  ctx.fillText("finntech3.github.io/degree-value", P, CARD_H - P + 10);
}
