import { gbp } from "../lib/format";
import { useWidth } from "./hooks";

interface Props {
  path: Record<string, [number | null, number | null, number | null]>;
  label: string;
}

const YEARS = [1, 3, 5, 10];

/** Median pay one to ten years out, with the middle half of graduates shaded. */
export function PayChart({ path, label }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>(460);
  const H = 290;
  const L = 44;
  const R = 16;
  const T = 24;
  const B = H - 40;
  const pts = YEARS.map((y) => ({ y, v: path[String(y)] })).filter((p) => p.v && p.v[1] !== null);
  const top = Math.max(...pts.map((p) => p.v![2] ?? p.v![1]!));
  const peak = Math.ceil(top / 20_000) * 20_000;
  const x = (y: number) => L + ((y - 1) / 9) * (W - L - R);
  const yy = (v: number) => B - (v / peak) * (B - T);
  const band =
    pts.map((p) => `${x(p.y)},${yy(p.v![2]!)}`).join(" ") +
    " " +
    [...pts]
      .reverse()
      .map((p) => `${x(p.y)},${yy(p.v![0]!)}`)
      .join(" ");
  const ticks = Array.from({ length: peak / 20_000 + 1 }, (_, i) => i * 20_000);

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="pay-desc">
        <desc id="pay-desc">
          {`Median pay of ${label} graduates: ` +
            pts.map((p) => `${gbp(p.v![1]!)} ${p.y} year${p.y > 1 ? "s" : ""} out`).join(", ") +
            ". The shaded band is the middle half of graduates."}
        </desc>
        {ticks.map((v) => (
          <g key={v}>
            <line className={v ? "c-grid" : "c-base"} x1={L} x2={W - R} y1={yy(v) + 0.5} y2={yy(v) + 0.5} />
            <text className="c-tick" x={L - 6} y={yy(v) + 4} textAnchor="end">
              {v ? `${v / 1000}k` : "0"}
            </text>
          </g>
        ))}
        <polygon points={band} className="c-band-fill" />
        <polyline
          points={pts.map((p) => `${x(p.y)},${yy(p.v![1]!)}`).join(" ")}
          fill="none"
          className="c-you-line"
          strokeWidth={2.5}
        />
        {pts.map((p) => (
          <g key={p.y}>
            <circle className="c-you" cx={x(p.y)} cy={yy(p.v![1]!)} r={4.5} />
            <text
              className="c-value c-halo"
              x={x(p.y) + (p.y === 1 ? 6 : p.y === 10 ? 4 : 0)}
              y={yy(p.v![1]!) + (p.y === 1 ? 24 : -12)}
              textAnchor={p.y === 1 ? "start" : p.y === 10 ? "end" : "middle"}
            >
              {gbp(p.v![1]!)}
            </text>
            <text className="c-tick" x={x(p.y)} y={B + 18} textAnchor="middle">
              {p.y}
            </text>
          </g>
        ))}
        <text className="c-note" x={L} y={B + 34}>
          years after graduating
        </text>
      </svg>
    </div>
  );
}
