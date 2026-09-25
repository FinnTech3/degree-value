// The result as a 1080 by 1350 picture, drawn in the browser; nothing is uploaded.

export interface CardContent {
  big: string;
  unit: string;
  subject: string;
  lines: string[];
  place: number;
}

const INK = "#14171a";
const TEXT = "#eef1f0";
const SOFT = "#bcc3c2";
const MUTED = "#939b9a";
const REST = "#434a49";
const YOU = "#3987e5";

const FONTS = [
  '700 280px "IBM Plex Sans Condensed"',
  '700 44px "IBM Plex Sans Condensed"',
  '600 52px "IBM Plex Sans"',
  '400 40px "IBM Plex Sans"',
  '400 32px "IBM Plex Mono"',
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

export function drawCard(canvas: HTMLCanvasElement, c: CardContent): void {
  canvas.width = 1080;
  canvas.height = 1350;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const P = 84;
  const inner = 1080 - 2 * P;
  ctx.fillStyle = INK;
  ctx.fillRect(0, 0, 1080, 1350);

  // the mark: forty years, the last one lit
  for (let i = 0; i < 10; i++) {
    ctx.fillStyle = i === 9 ? TEXT : REST;
    ctx.fillRect(P + i * 12, P + 8, 8, 32);
  }
  ctx.fillStyle = TEXT;
  ctx.font = '700 44px "IBM Plex Sans Condensed", sans-serif';
  ctx.fillText("Degree value", P + 136, P + 40);

  ctx.fillStyle = SOFT;
  ctx.font = '400 40px "IBM Plex Sans", sans-serif';
  let y = P + 150;
  for (const line of wrap(
    ctx,
    `A Plan 5 student loan, ${c.subject}, a graduate at the ${c.place}th place in 100`,
    inner,
  )) {
    ctx.fillText(line, P, y);
    y += 52;
  }
  ctx.fillStyle = TEXT;
  ctx.font = '700 280px "IBM Plex Sans Condensed", sans-serif';
  ctx.fillText(c.big, P - 8, y + 240);
  ctx.font = '600 52px "IBM Plex Sans", sans-serif';
  ctx.fillText(c.unit, P, y + 320);
  y += 420;
  ctx.font = '400 40px "IBM Plex Sans", sans-serif';
  for (const text of c.lines) {
    for (const line of wrap(ctx, text, inner)) {
      ctx.fillText(line, P, y);
      y += 52;
    }
    y += 18;
  }

  // forty years as a strip, the years repaid lit
  const years = Number.parseInt(c.big, 10) || 0;
  const slot = inner / 40;
  for (let i = 0; i < 40; i++) {
    ctx.fillStyle = i < years ? YOU : REST;
    ctx.beginPath();
    ctx.roundRect(P + i * slot + 2, 1350 - P - 170, slot - 4, 60, 3);
    ctx.fill();
  }
  ctx.fillStyle = MUTED;
  ctx.font = '400 28px "IBM Plex Sans", sans-serif';
  ctx.fillText("each block is a year of repayments, forty at most", P, 1350 - P - 80);
  ctx.font = '400 32px "IBM Plex Mono", monospace';
  ctx.fillText("finntech3.github.io/degree-value", P, 1350 - P);
}
