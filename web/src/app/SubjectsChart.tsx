import type { Subject } from "../lib/degree";
import { useWidth } from "./hooks";

interface Props {
  subjects: Subject[];
  current: string;
  term: number;
}

/** Every subject as a dot at its median years repaying, stacked where they tie. */
export function SubjectsChart({ subjects, current, term }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const L = 10;
  const R = 10;
  const r = W < 520 ? 6 : 7;
  const gap = 2 * r + 3;
  const lo = 10;
  const x = (v: number) => L + ((v - lo) / (term - lo)) * (W - L - R);
  const stacks = new Map<number, Subject[]>();
  for (const s of [...subjects].sort((a, b) => a.full - b.full)) {
    const k = Math.round(x(s.years) / gap);
    stacks.set(k, [...(stacks.get(k) ?? []), s]);
  }
  const tallest = Math.max(...[...stacks.values()].map((v) => v.length));
  const B = 30 + tallest * gap + 10;
  const H = B + 44;
  const cur = subjects.find((s) => s.name === current)!;
  let youXY: [number, number] = [0, 0];
  const dots: JSX.Element[] = [];
  for (const [, group] of stacks) {
    group.forEach((s, i) => {
      const cx = x(s.years);
      const cy = B - r - 2 - i * gap;
      if (s.name === current) youXY = [cx, cy];
      dots.push(<circle key={s.name} className={s.name === current ? "c-you" : "c-rest"} cx={cx} cy={cy} r={r} />);
    });
  }
  const end = youXY[0] > W * 0.6;
  const off = subjects.filter((s) => s.years >= term).length;

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="subj-desc">
        <desc id="subj-desc">
          {`Median years repaying for each of ${subjects.length} subjects, from ${Math.min(...subjects.map((s) => s.years))} ` +
            `to ${term}. ${off} subjects are at ${term}, written off. ${current}: ${cur.years} years.`}
        </desc>
        {dots}
        <line className="c-base" x1={L} x2={W - R} y1={B + 0.5} y2={B + 0.5} />
        {[10, 20, 30, 40].map((v) => (
          <text key={v} className="c-tick" x={x(v)} y={B + 18} textAnchor="middle">
            {v}
          </text>
        ))}
        <text className="c-note" x={L} y={B + 36}>
          median years repaying
        </text>
        <text className="c-note" x={W - R} y={B + 36} textAnchor="end">
          written off
        </text>
        <line className="c-you-line" x1={youXY[0]} x2={youXY[0]} y1={16} y2={youXY[1] - r - 2} />
        <text className="c-strong c-halo" x={youXY[0] + (end ? -8 : 8)} y={20} textAnchor={end ? "end" : "start"}>
          {`${current}: ${cur.years}`}
        </text>
      </svg>
    </div>
  );
}
