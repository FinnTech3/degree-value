import type { DegreeFile, Places } from "../lib/degree";
import { useWidth } from "./hooks";

interface Props {
  d: DegreeFile;
  places: Places;
  place: number;
  subject: string;
}

/** Years repaying at every place among the subject's graduates, with the reader marked. */
export function PlaceChart({ d, places, place, subject }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const H = W < 520 ? 250 : 280;
  const L = 34;
  const R = 10;
  const T = 30;
  const B = H - 44;
  const qs = d.places.map((q) => Math.round(q * 100));
  const x = (q: number) => L + ((q - 5) / 90) * (W - L - R);
  const y = (yrs: number) => B - (yrs / d.term) * (B - T);
  const pts = qs.map((q, i) => `${x(q).toFixed(1)},${y(places.years[i]!).toFixed(1)}`).join(" ");
  const i = qs.indexOf(place);
  const you = places.years[i]!;
  const firstClear = places.cleared.findIndex((c) => c);

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="place-desc">
        <desc id="place-desc">
          {`Years a ${subject} graduate repays, by where they land among the subject's graduates. ` +
            (firstClear < 0
              ? "Nobody in the range clears the loan before it is written off."
              : `Below the ${qs[firstClear]}th place the loan runs the full ${d.term} years; above it, it is cleared, ` +
                `in ${places.years[places.years.length - 1]} years at the 95th place.`) +
            ` At your place, ${place}th, it runs ${you} years.`}
        </desc>
        {[0, 10, 20, 30, 40].map((v) => (
          <g key={v}>
            <line className={v ? "c-grid" : "c-base"} x1={L} x2={W - R} y1={y(v) + 0.5} y2={y(v) + 0.5} />
            <text className="c-tick" x={L - 6} y={y(v) + 4} textAnchor="end">
              {v}
            </text>
          </g>
        ))}
        <text className="c-note" x={L} y={T - 12}>
          years repaying; {d.term} means written off at {d.graduation_age + d.term}
        </text>
        <polyline points={pts} fill="none" className="c-rest-line" strokeWidth={3} strokeLinejoin="round" />
        <line className="c-you-line" x1={x(place)} x2={x(place)} y1={y(you)} y2={B} strokeDasharray="3 3" />
        <circle className="c-panel" cx={x(place)} cy={y(you)} r={9} />
        <circle className="c-you" cx={x(place)} cy={y(you)} r={7} />
        {[5, 25, 50, 75, 95].map((q) => (
          <text key={q} className="c-tick" x={x(q)} y={B + 18} textAnchor="middle">
            {q}
          </text>
        ))}
        <text className="c-note" x={L} y={B + 36}>
          lowest paid
        </text>
        <text className="c-note" x={W - R} y={B + 36} textAnchor="end">
          highest paid
        </text>
      </svg>
    </div>
  );
}
