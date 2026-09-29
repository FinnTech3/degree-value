import { useEffect, useMemo, useState } from "react";
import {
  type DegreeFile,
  PLACE_MAX,
  PLACE_MIN,
  type Sex,
  type Subject,
  clearingPlace,
  outcome,
  shareBelow,
  slug,
  universities,
} from "../lib/degree";
import { gbp } from "../lib/format";
import { readChoice, writeChoice } from "../lib/url";
import { FoilNote } from "./FoilNote";
import { Loom } from "./Loom";
import { PayChart } from "./PayChart";
import { PlaceChart } from "./PlaceChart";
import { ShareCard } from "./ShareCard";
import { UniChart } from "./UniChart";
import { useCountUp } from "./hooks";
import { Monogram } from "./series/Monogram";
import { SeriesStrip } from "./series/SeriesStrip";
import { PORTFOLIO } from "./series/series";

const REPO = "https://github.com/FinnTech3/degree-value";
const GROUPS: [Sex, string][] = [
  ["Total", "All"],
  ["Female", "Women"],
  ["Male", "Men"],
];
const WHO: Record<Sex, string> = { Total: "graduates", Female: "women graduates", Male: "men graduates" };

function ordinal(n: number): string {
  const s = n % 100 >= 11 && n % 100 <= 13 ? "th" : (["th", "st", "nd", "rd"][n % 10] ?? "th");
  return `${n}${s}`;
}

function pct(x: number): string {
  return `${Math.round(100 * x)}%`;
}

function useTheme() {
  const [theme, setTheme] = useState<string | undefined>(() => document.documentElement.dataset.theme);
  const systemDark = typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = theme ? theme === "dark" : systemDark;
  function toggle() {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Private windows may refuse; the choice then lasts for this visit only.
    }
    setTheme(next);
  }
  return { dark, toggle };
}

export function App() {
  const [d, setD] = useState<DegreeFile | null>(null);
  const [failed, setFailed] = useState(false);
  const first = useMemo(() => readChoice(location.search), []);
  const [subjectSlug, setSubjectSlug] = useState<string | null>(first.subject);
  const [sex, setSex] = useState<Sex>(first.sex);
  const [place, setPlace] = useState(first.place);
  const [uni, setUni] = useState<number | null>(first.uni);
  const theme = useTheme();

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/degree.json`)
      .then((r) => r.json() as Promise<DegreeFile>)
      .then(setD)
      .catch(() => setFailed(true));
  }, []);

  const subject: Subject | null = useMemo(() => {
    if (!d) return null;
    const bySlug = d.subjects.find((s) => slug(s.name) === subjectSlug);
    return bySlug ?? [...d.subjects].sort((a, b) => b.graduates - a.graduates)[0]!;
  }, [d, subjectSlug]);

  useEffect(() => {
    if (!d || !subject) return;
    const s = slug(subject.name);
    history.replaceState(null, "", `${location.pathname}${writeChoice({ subject: s, sex, place, uni })}`);
  }, [d, subject, sex, place, uni]);

  const sorted = useMemo(() => (d ? [...d.subjects].sort((a, b) => a.name.localeCompare(b.name, "en-GB")) : []), [d]);

  const you = useMemo(() => {
    if (!d || !subject) return null;
    const o = outcome(d, subject, sex, place);
    if (!o || (o.years === subject.years && o.cleared === subject.cleared)) return null;
    return {
      age: o.age,
      cleared: o.cleared,
      label: o.cleared ? `you clear it at ${o.age}` : `you: still owed at ${d.graduation_age + d.term}`,
    };
  }, [d, subject, sex, place]);

  return (
    <div className="wrap">
      <header className="bar">
        <Monogram />
        <p className="series">
          A series of six by <b>Finn Lakin</b>
          <br />
          No. 2 · Student loans
        </p>
        <button
          className="toggle"
          type="button"
          onClick={theme.toggle}
          aria-label={`Switch to ${theme.dark ? "light" : "dark"} theme`}
        >
          {theme.dark ? "Light" : "Dark"}
        </button>
      </header>

      <main>
        <div className="stage">
          <div className="head">
            <h1>
              Some loans run <em>forty years.</em>
            </h1>
            <p className="dek">
              Each thread is a subject: what its typical graduate still owes on a Plan 5 loan, from 21 to 61. It knots
              where the loan is cleared, and frays off the edge where it is written off instead.
            </p>
          </div>

          <FoilNote>
            I'm a student, somewhere inside this exact maze of thresholds, interest and forty-year write-offs. Every
            calculator I found skipped the interest or hid its working, so I built the one I wanted. Pick your subject
            and see yours.
          </FoilNote>

          <figure className="loom-fig">
            {d && subject ? (
              <Loom
                d={d}
                current={subject.name}
                you={you}
                onPick={(name) => {
                  setSubjectSlug(slug(name));
                  setUni(null);
                }}
              />
            ) : (
              <p className="waiting">
                {failed ? "The data did not load. Refresh the page to try again." : "Threading 34 subjects"}
              </p>
            )}
          </figure>

          <div className="side">
            <div className="controls">
              <div className="field">
                <label htmlFor="subject">Your subject, or tap its thread</label>
                <select
                  id="subject"
                  value={subject ? slug(subject.name) : ""}
                  disabled={!d}
                  onChange={(e) => {
                    setSubjectSlug(e.target.value);
                    setUni(null);
                  }}
                >
                  {!d && <option value="">Loading subjects</option>}
                  {sorted.map((s) => (
                    <option key={s.name} value={slug(s.name)}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field inline">
                <span id="group-label">Graduates</span>
                <div className="segmented" role="group" aria-labelledby="group-label">
                  {GROUPS.map(([k, label]) => (
                    <button key={k} type="button" aria-pressed={sex === k} onClick={() => setSex(k)}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="field slider">
                <label htmlFor="place">
                  Where you land among {subject ? subject.name : "your subject's"} {WHO[sex]}:{" "}
                  <output htmlFor="place">{place === 50 ? "the middle" : `${ordinal(place)} of 100`}</output>
                </label>
                <input
                  id="place"
                  type="range"
                  min={PLACE_MIN}
                  max={PLACE_MAX}
                  step={1}
                  value={place}
                  onChange={(e) => setPlace(Number(e.target.value))}
                />
                <div className="ends" aria-hidden="true">
                  <span>lower paid</span>
                  <span>higher paid</span>
                </div>
              </div>
            </div>

            <div className={d && subject ? "answer" : "answer skeleton"} aria-live="polite">
              {failed ? (
                <p>The data did not load. Refresh the page to try again.</p>
              ) : d && subject ? (
                <Answer d={d} s={subject} sex={sex} place={place} />
              ) : (
                <p>Loading every subject</p>
              )}
            </div>
          </div>
        </div>

        {d && subject && <Sections d={d} s={subject} sex={sex} place={place} uni={uni} setUni={setUni} />}

        {d && subject && (
          <aside className="signoff">
            <p>That's your number, worked out the way I wished a calculator had done it for me.</p>
          </aside>
        )}

        <SeriesStrip here="degree-value" />
      </main>

      <footer>
        <p>
          Sources: DfE, Graduate outcomes (LEO): provider level data and national tables, 2022-23 tax year; DfE, Student
          loan forecasts for England 2024-25; ONS, Annual Survey of Hours and Earnings 2025 and average weekly earnings;
          OBR, Economic and fiscal outlook, March 2026.
        </p>
        <p>
          A projection, not a promise. Pay is what graduates earned in the 2022-23 tax year, followed on by age, and it
          says nothing about what a particular person would have earned without the degree. The model holds each
          graduate at the same place among their subject's graduates for life, and gives the lowest places, those not in
          sustained work or study five years out, no earnings.
        </p>
        <p>
          Made by Finn Lakin. The method, the code and every check are at{" "}
          <a href={REPO}>github.com/FinnTech3/degree-value</a>, and the rest of my work is at{" "}
          <a href={PORTFOLIO}>finn-lakin-portfolio.netlify.app</a>. No cookies, no tracking.
        </p>
      </footer>
    </div>
  );
}

function Answer({ d, s, sex, place }: { d: DegreeFile; s: Subject; sex: Sex; place: number }) {
  const o = outcome(d, s, sex, place)!;
  const shown = useCountUp(o.years);
  const path = s.paths[sex];
  return (
    <>
      <div className="answer-main">
        <div className="where">
          <b>{s.name}</b>
          <span>{`${place === 50 ? "the middle" : `${ordinal(place)} of 100`} among ${WHO[sex]}`}</span>
        </div>
        <div className="big">
          <span className="num">{Math.round(shown ?? o.years)} years</span>
          <span className="unit">{o.repaid === 0 ? "of holding a Plan 5 loan" : "of repaying a Plan 5 loan"}</span>
        </div>
        <p className="context">
          {o.cleared
            ? `Cleared in ${o.taxYear}, at ${o.age}.`
            : o.repaid === 0
              ? `Never earns above the threshold, so nothing is ever repaid. The whole loan is written off at ${o.age}, in ${o.taxYear}.`
              : `Still repaying at ${o.age}, when what is left is written off, in ${o.taxYear}.`}
        </p>
      </div>
      <div className="answer-side">
        <dl className="facts">
          <div>
            <dt>Repaid in total, at 2024-25 prices</dt>
            <dd>{gbp(o.repaid)}</dd>
          </div>
          <div>
            <dt>Typical pay a year out, then ten years out</dt>
            <dd>{`${gbp(path["1"]?.[1] ?? 0)} → ${gbp(path["10"]?.[1] ?? 0)}`}</dd>
          </div>
          <div>
            <dt>{`${s.name} graduates who clear it`}</dt>
            <dd>{pct(s.full)}</dd>
          </div>
        </dl>
        <p className="note">
          {`Starting from the DfE's average balance of ${gbp(d.balance)} when repayments begin in April ${d.first_year}.`}
        </p>
      </div>
    </>
  );
}

function Sections({
  d,
  s,
  sex,
  place,
  uni,
  setUni,
}: {
  d: DegreeFile;
  s: Subject;
  sex: Sex;
  place: number;
  uni: number | null;
  setUni: (u: number | null) => void;
}) {
  const unis = useMemo(() => universities(d, s), [d, s]);
  const withFive = unis.filter((u) => u.y5 !== null);
  const chosen = uni !== null && uni < d.providers.length ? d.providers[uni]![0] : null;
  const chosenUni = unis.find((u) => u.name === chosen);
  const o = outcome(d, s, sex, place)!;
  const clearsFrom = clearingPlace(d, s, sex);
  const card = useMemo(
    () => ({
      years: o.years,
      cleared: o.cleared,
      age: o.age,
      subject: s.name,
      place,
      lines: [
        o.repaid === 0
          ? "Never earns above the threshold, so nothing is ever repaid."
          : `${gbp(o.repaid)} repaid in total, at 2024-25 prices.`,
        `${pct(s.full)} of ${s.name} graduates clear their loan before it is written off.`,
      ],
      subjects: d.subjects,
      start: d.balance_real,
      graduationAge: d.graduation_age,
      term: d.term,
    }),
    [o, s, place, d],
  );

  return (
    <>
      <section>
        <h2>Your place, and everyone else's</h2>
        <p className="sub">
          {clearsFrom === null
            ? `No ${WHO[sex]} in this subject between the 5th and 95th place clear the loan before it is written off.`
            : clearsFrom <= PLACE_MIN
              ? `Every place on the slider clears the loan before it is written off; the better paid, the sooner.`
              : `Below the ${ordinal(clearsFrom)} place, ${s.name} ${WHO[sex]} are still repaying when the loan is written off. Above it, they clear it, and the better paid, the sooner.`}
        </p>
        <div className="fig">
          <PlaceChart d={d} places={s.places[sex]!} place={place} subject={s.name} />
        </div>
        <p className="note" style={{ marginTop: 10 }}>
          {`The lowest ${Math.round(100 * (s.not_working[sex] ?? 0))} in 100 were not in sustained work or study five years out, so the model gives them no earnings and they repay nothing.`}
        </p>
      </section>

      <section>
        <div>
          <h2>Starting pay is a poor guide</h2>
          <p className="sub">
            {s.rank1 && s.rank10
              ? `${s.name} ranks ${ordinal(s.rank1)} of 34 subjects for pay a year out and ${ordinal(s.rank10)} ten years out. Median pay, with the middle half of ${WHO[sex]} shaded.`
              : `Median pay, with the middle half of ${WHO[sex]} shaded.`}
          </p>
          <div className="fig">
            <PayChart path={s.paths[sex]} label={`${s.name} ${WHO[sex]}`} />
          </div>
        </div>
      </section>

      <section>
        <h2>{`${s.name} at each university`}</h2>
        <p className="sub">
          {`Median pay five years after graduating, where the DfE publishes it: ${withFive.length} universities and colleges. Small groups are left out by the DfE, and a university's figure says as much about who it admits as what it teaches.`}
        </p>
        <div className="council-pick" style={{ marginBottom: 12 }}>
          <label htmlFor="uni">Your university:</label>
          <select
            id="uni"
            value={chosen ?? ""}
            onChange={(e) => {
              const i = d.providers.findIndex(([n]) => n === e.target.value);
              setUni(i >= 0 ? i : null);
            }}
          >
            <option value="">Choose</option>
            {[...unis]
              .sort((a, b) => a.name.localeCompare(b.name, "en-GB"))
              .map((u) => (
                <option key={u.name} value={u.name}>
                  {u.name}
                </option>
              ))}
          </select>
        </div>
        <div className="fig">
          <UniChart unis={unis} chosen={chosen} subject={s.name} />
        </div>
        {chosenUni && (
          <p className="compare">
            {chosenUni.y5 === null
              ? `The DfE does not publish a five-year figure for ${s.name} at ${chosenUni.name}, usually because too few graduates are in it.`
              : `${chosenUni.name}: ${gbp(chosenUni.y5)} five years out, from ${chosenUni.n5 ?? "an unpublished number of"} graduates in the figure. That is above ${pct(shareBelow(unis, chosenUni.y5))} of the universities shown.`}
          </p>
        )}
      </section>

      <section>
        <h2>How I know these numbers are right</h2>
        <p className="sub">
          The earnings are checked against what the DfE published, and the loan model against the DfE's own forecast,
          including where it falls short.
        </p>
        <ul className="checks">
          {d.checks.map((c) => (
            <li key={c.name}>
              <span className={c.passed ? "pill" : "pill fail"}>{c.passed ? "Pass" : "Fail"}</span>
              <div>
                <b>
                  {c.name === "published provider ranges"
                    ? "The DfE's own published ranges, rebuilt from its raw file"
                    : "The national headline figures, rebuilt"}
                </b>
                <span>
                  {c.name === "published provider ranges"
                    ? "All 8 numbers reproduced exactly: pay and employment ranges across universities, overall and for women and men."
                    : "Median pay five years out, the share in work or study, and the gap between men's and women's pay, all to the published digit."}
                </span>
              </div>
            </li>
          ))}
          <li>
            <span className="pill neutral">Tuned</span>
            <div>
              <b>The loan model, against the DfE's forecast</b>
              <span>
                {`One number is set, pay growth after 2030, so that ${pct(d.model.full_repayment_share)} repay in full, as the DfE forecasts. Then, untuned: the median graduate repays for ${d.model.median_years} years (DfE ${d.dfe.median_years}), and lifetime repayments come out ${Math.round(100 * (1 - d.model.repayments_real / d.dfe.repayments_real))}% below the DfE's. The best-paid half finishes a few years sooner than the DfE expects.`}
              </span>
            </div>
          </li>
        </ul>
      </section>

      <section>
        <h2>Save your result</h2>
        <ShareCard content={card} file={`degree-value-${slug(s.name)}.png`} />
      </section>
    </>
  );
}
