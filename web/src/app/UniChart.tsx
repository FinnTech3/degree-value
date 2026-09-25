import type { University } from "../lib/degree";
import { gbp } from "../lib/format";
import { useWidth } from "./hooks";

interface Props {
  unis: University[];
  chosen: string | null;
  subject: string;
}

/** Each university's median pay five years out in the subject, one dot each, stacked where they would overlap. */
export function UniChart({ unis, chosen, subject }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const known = unis.filter((u) => u.y5 !== null).sort((a, b) => a.y5! - b.y5!);
  if (!known.length) {
    return <p className="note">The DfE publishes no five-year figure for any university in this subject.</p>;
  }
  const L = 12;
  const R = 24;
  const r = 5;
  const gap = 2 * r + 2;
  const lo = Math.floor(known[0]!.y5! / 10_000) * 10_000;
  const hi = Math.ceil(known[known.length - 1]!.y5! / 10_000) * 10_000;
  const x = (v: number) => L + ((v - lo) / Math.max(1, hi - lo)) * (W - L - R);

  const heights = new Map<number, number>();
  const placed = known.map((u) => {
    const k = Math.round(x(u.y5!) / gap);
    const level = heights.get(k) ?? 0;
    heights.set(k, level + 1);
    return { u, cx: k * gap, level };
  });
  const tallest = Math.max(...heights.values());
  const base = 44 + tallest * gap + 4;
  const H = base + 56;
  const cy = (level: number) => base - r - 2 - level * gap;
  const pick = placed.find((p) => p.u.name === chosen);
  // flip the label to the left of the dot when it would run off the right edge
  const labelWidth = pick ? (pick.u.name.length + 9) * 7.6 : 0;
  const end = pick ? pick.cx + 8 + labelWidth > W - 4 && pick.cx - 8 - labelWidth >= 0 : false;
  const ticks: number[] = [];
  for (let v = lo; v <= hi; v += 10_000) ticks.push(v);

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="uni-desc">
        <desc id="uni-desc">
          {`Median pay five years after graduating in ${subject} at ${known.length} universities, from ` +
            `${gbp(known[0]!.y5!)} to ${gbp(known[known.length - 1]!.y5!)}.` +
            (pick ? ` ${pick.u.name}: ${gbp(pick.u.y5!)}.` : "")}
        </desc>
        {placed.map((p, i) => (
          <circle key={p.u.name + i} className={p === pick ? "c-you" : "c-rest-dot"} cx={p.cx} cy={cy(p.level)} r={r} />
        ))}
        <line className="c-base" x1={L} x2={W - R} y1={base + 0.5} y2={base + 0.5} />
        {ticks.map((v) => (
          <text key={v} className="c-tick" x={x(v)} y={base + 18} textAnchor="middle">
            {`${v / 1000}k`}
          </text>
        ))}
        {pick && (
          <>
            <line className="c-you-line" x1={pick.cx} x2={pick.cx} y1={22} y2={cy(pick.level) - r - 2} />
            <text className="c-strong c-halo" x={pick.cx + (end ? -8 : 8)} y={26} textAnchor={end ? "end" : "start"}>
              {`${pick.u.name}: ${gbp(pick.u.y5!)}`}
            </text>
          </>
        )}
        <text className="c-note" x={L} y={base + 38}>
          median pay five years out, one dot per university
        </text>
      </svg>
    </div>
  );
}
