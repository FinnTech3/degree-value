import { type PointerEvent, useMemo, useState } from "react";
import type { DegreeFile, Subject } from "../lib/degree";
import { gbp } from "../lib/format";
import { useWidth } from "./hooks";

interface Props {
  d: DegreeFile;
  current: string;
  onPick: (name: string) => void;
  /** The reader's own loan, marked on their subject's thread. */
  you: { age: number; cleared: boolean; label: string } | null;
}

interface Row {
  s: Subject;
  /** Balance at 21, then at the end of each year. */
  owed: number[];
}

/** A line through the points as gentle curves, so a thread reads as thread rather than a bar. */
function smooth(p: [number, number][]): string {
  let out = `${p[0]![0].toFixed(1)},${p[0]![1].toFixed(2)}`;
  for (let i = 0; i < p.length - 1; i++) {
    const [a, b, c, e] = [p[i - 1] ?? p[i]!, p[i]!, p[i + 1]!, p[i + 2] ?? p[i + 1]!];
    const c1 = [b[0] + (c[0] - a[0]) / 6, b[1] + (c[1] - a[1]) / 6];
    const c2 = [c[0] - (e[0] - b[0]) / 6, c[1] - (e[1] - b[1]) / 6];
    out += `C${c1[0]!.toFixed(1)},${c1[1]!.toFixed(2)} ${c2[0]!.toFixed(1)},${c2[1]!.toFixed(2)} ${c[0].toFixed(1)},${c[1].toFixed(2)}`;
  }
  return out;
}

/** Rows from the quickest to clear at the top to the ones written off at the bottom. */
export function order(subjects: Subject[], start: number): Row[] {
  return [...subjects]
    .sort((a, b) => a.years - b.years || Number(b.cleared) - Number(a.cleared) || b.full - a.full)
    .map((s) => ({ s, owed: [start, ...s.thread] }));
}

/** The age a subject's typical graduate still owes at, and what, or null once it is cleared. */
export function owedAt(row: Row, years: number): number | null {
  if (years >= row.owed.length) return null;
  const b = row.owed[years]!;
  return b > 0 ? b : null;
}

/**
 * Every subject as a thread from 21 to 61. A thread is as thick as what its
 * typical graduate still owes, in today's money, so it swells while interest
 * outruns repayments, thins as they catch up, and ends in a knot where the
 * loan is cleared. The ones still owed at 61 run off the edge and fray.
 */
export function Loom({ d, current, onPick, you }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>(360);
  const rows = useMemo(() => order(d.subjects, d.balance_real), [d]);
  const [age, setAge] = useState(40);
  const [hover, setHover] = useState<string | null>(null);

  const start = d.graduation_age;
  const end = start + d.term;
  const narrow = W < 600;
  const rowH = narrow ? 12 : 16;
  const T = 60;
  const L = 6;
  const R = 10;
  const B = T + rows.length * rowH;
  const H = B + 26;
  const maxOwed = Math.max(...rows.flatMap((r) => r.owed));
  const maxT = rowH * 0.58;
  const x = (a: number) => L + ((a - start) / d.term) * (W - L - R);
  const cy = (i: number) => T + i * rowH + rowH / 2;
  const thick = (b: number) => Math.max(0.5, (b / maxOwed) * maxT);
  // Every loan starts the same size, so the threads leave one spool at 21 and
  // fan out to their rows over the first few years.
  const middle = (T + B) / 2;
  const FAN = 5;
  const lane = (i: number, k: number) => {
    const t = Math.min(1, k / FAN);
    return middle + (cy(i) - middle) * (t * t * (3 - 2 * t));
  };
  const chars = narrow ? 7 : 7.6;

  /** A label kept inside the loom: ending at `at` if it fits, else starting at the left edge. */
  function place(text: string, at: number): { x: number; anchor: "start" | "end" } {
    return at - text.length * chars < L ? { x: L, anchor: "start" } : { x: at, anchor: "end" };
  }

  /** A label sits above its thread, unless that would run into the ages along the top. */
  function labelY(i: number): number {
    const above = cy(i) - rowH * 0.62;
    return above < T + 4 ? cy(i) + rowH * 0.62 + 11 : above;
  }

  function thread(r: Row, i: number): string {
    const top: [number, number][] = [];
    const bottom: [number, number][] = [];
    const perYear = (W - L - R) / d.term;
    r.owed.forEach((b, k) => {
      const px = x(start + k);
      // Measured across the thread, not straight up, so a thread keeps its
      // thickness through the fan instead of pinching where it slopes.
      const t = Math.min(1, k / FAN);
      const slope = k < FAN ? ((cy(i) - middle) * 6 * t * (1 - t)) / FAN / perYear : 0;
      const h = b > 0 ? (thick(b) / 2) * Math.sqrt(1 + slope * slope) : 0;
      top.push([px, lane(i, k) - h]);
      bottom.unshift([px, lane(i, k) + h]);
    });
    return `M${smooth(top)}L${smooth(bottom)}Z`;
  }

  const years = age - start;
  const done = rows.filter((r) => owedAt(r, years) === null && r.s.cleared).length;
  const owing = rows.map((r) => owedAt(r, years)).filter((b): b is number => b !== null);
  const readout =
    owing.length === 0
      ? `At ${age}, every subject's typical graduate has cleared the loan or had it written off.`
      : `At ${age}, the typical graduate has cleared the loan in ${done} of ${rows.length} subjects. ` +
        `In the other ${owing.length} they still owe between ${gbp(Math.min(...owing))} and ${gbp(Math.max(...owing))}, in today's money.`;

  function locate(e: PointerEvent<SVGSVGElement>) {
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    const py = ((e.clientY - box.top) / box.height) * H;
    const i = Math.floor((py - T) / rowH);
    const a = Math.round(start + ((px - L) / (W - L - R)) * d.term);
    return { row: i >= 0 && i < rows.length ? rows[i]!.s.name : null, age: Math.min(end, Math.max(start, a)) };
  }

  const ci = rows.findIndex((r) => r.s.name === current);
  const cur = rows[ci]!;
  const hi = hover ? rows.findIndex((r) => r.s.name === hover) : -1;
  const curEnd = start + cur.s.years;
  const curText = cur.s.cleared ? `${cur.s.name}: cleared at ${curEnd}` : `${cur.s.name}: still owed at ${end}`;
  const curLabel = place(curText, Math.min(W - R, x(curEnd) + 4));
  const cleared = rows.filter((r) => r.s.cleared);
  const quickest = rows[0]!;

  return (
    <div ref={ref} className="loom-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width={W}
        height={H}
        className="loom"
        role="img"
        aria-labelledby="loom-desc"
        onPointerMove={(e) => {
          const at = locate(e);
          setHover(at.row);
          if (e.pointerType === "mouse" || e.buttons) setAge(at.age);
        }}
        onPointerLeave={() => setHover(null)}
        onPointerDown={(e) => {
          const at = locate(e);
          setAge(at.age);
          if (at.row) onPick(at.row);
        }}
      >
        <desc id="loom-desc">
          {`${rows.length} threads, one for each subject, showing what its typical graduate still owes on a Plan 5 loan from ${start} to ${end}. ` +
            `${cleared.length} end in a knot where the loan is cleared, from ${quickest.s.name} at ${start + quickest.s.years}; ` +
            `${rows.length - cleared.length} are still owed at ${end} and written off. ${current} is picked out: ` +
            (cur.s.cleared ? `cleared at ${curEnd}.` : `still owed at ${end}.`)}
        </desc>
        <defs>
          <linearGradient id="foil-thread" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" className="foil-a" />
            <stop offset="0.5" className="foil-b" />
            <stop offset="1" className="foil-c" />
          </linearGradient>
        </defs>

        {/* the loom's frame: a warp line every five years */}
        {Array.from({ length: d.term / 5 + 1 }, (_, k) => start + 5 * k).map((a) => (
          <g key={a}>
            <line className="warp" x1={x(a)} x2={x(a)} y1={T - 6} y2={B + 4} />
            {(a % 10 === 1 || a === end) && (
              <text className="c-tick" x={x(a)} y={T - 14} textAnchor="middle">
                {a}
              </text>
            )}
          </g>
        ))}
        <text className="c-note" x={L} y={14}>
          age, and what the typical graduate still owes
        </text>

        {rows.map((r, i) => {
          const isCur = i === ci;
          if (isCur) return null;
          const last = r.owed.length - 1;
          return (
            <g key={r.s.name} className={i === hi ? "thread hover" : r.s.cleared ? "thread" : "thread off"}>
              <path d={thread(r, i)} />
              {r.s.cleared ? (
                <circle cx={x(start + last)} cy={cy(i)} r={narrow ? 1.6 : 2} />
              ) : (
                <path
                  className="fray"
                  d={`M${x(end)},${cy(i)}l5,-2.4M${x(end)},${cy(i)}l5.6,0M${x(end)},${cy(i)}l5,2.4`}
                />
              )}
            </g>
          );
        })}

        {/* the reader's subject, lifted, in foil */}
        <g className="thread current">
          <path d={thread(cur, ci)} fill="url(#foil-thread)" />
          {cur.s.cleared ? (
            <circle cx={x(curEnd)} cy={cy(ci)} r={narrow ? 2.6 : 3.2} />
          ) : (
            <path className="fray" d={`M${x(end)},${cy(ci)}l6,-3M${x(end)},${cy(ci)}l7,0M${x(end)},${cy(ci)}l6,3`} />
          )}
          <text className="c-strong c-halo" x={curLabel.x} y={labelY(ci)} textAnchor={curLabel.anchor}>
            {curText}
          </text>
        </g>

        {you && (
          <g className="you-mark">
            <line x1={x(you.age)} x2={x(you.age)} y1={cy(ci) - rowH} y2={cy(ci) + rowH} />
            <text className="c-value c-halo" x={x(you.age)} y={cy(ci) + rowH + 11} textAnchor="middle">
              {you.label}
            </text>
          </g>
        )}

        {hi >= 0 &&
          hi !== ci &&
          (() => {
            const h = rows[hi]!.s;
            const text = h.cleared ? `${h.name}: cleared at ${start + h.years}` : `${h.name}: written off`;
            const at = place(text, Math.min(W - R, x(start + h.years) + 4));
            return (
              <text className="c-label c-halo" x={at.x} y={labelY(hi)} textAnchor={at.anchor}>
                {text}
              </text>
            );
          })()}

        {/* the scrubber */}
        <line className="cursor" x1={x(age)} x2={x(age)} y1={T - 8} y2={B + 6} />
        <text
          className="c-strong c-halo"
          x={x(age)}
          y={T - 26}
          textAnchor={age > end - 3 ? "end" : age < start + 3 ? "start" : "middle"}
        >
          {`age ${age}`}
        </text>
      </svg>

      <div className="scrub">
        <label htmlFor="age">Scrub through a career</label>
        <input
          id="age"
          type="range"
          min={start}
          max={end}
          value={age}
          onChange={(e) => setAge(Number(e.target.value))}
          aria-valuetext={`age ${age}`}
        />
        <p className="readout" aria-live="polite">
          {readout}
        </p>
      </div>
    </div>
  );
}
