# Design decisions

The questions I would expect to be asked about this, and the answers.

## Why the student loan rather than the value of a degree?

Because the loan can be measured and the value cannot, not from this data.
LEO says what each subject's graduates earned. It does not say what the same
people would have earned otherwise, and the gap between graduates and
non-graduates (£42,000 against £30,500 in 2024) mixes what a degree adds with
who goes to university. The loan is different: given a path of earnings, what
Plan 5 takes is arithmetic, and the DfE publishes its own forecast to check it
against.

## Why tune anything?

Because pay growth after 2030 is unknowable and matters enormously. With the
OBR's long-run assumption two thirds of graduates cleared their loans; the DfE
forecasts 56%. Rather than choose a number, I set the one that reproduces the
DfE's share and judged the model on everything else. Tuning one number to one
target and then showing where the rest misses is more honest than a model with
no free parameters that quietly disagrees with the government's own forecast.

## Why keep each graduate at the same place for life?

It is the simplest assumption that reproduces LEO's quartiles exactly in every
year, and it makes each subject's results exact rather than simulated. It is
also the cause of the model's two known misses: too little repaid at the
bottom, too fast at the top. Letting places move from year to year fixes the
bottom and overshoots the total by 11%. No single setting matches everything,
so the central results use fixed places, the README marks where each subject
lands with places moving, and the tests pin both misses.

## Why subject, and not university and subject together?

The loan runs forty years, and only the national LEO file follows graduates to
ten years out, by subject. University figures stop at five years, and many are
suppressed. A forty-year projection from five years of one university's
graduates would be mostly assumption. The tool shows each university's
five-year pay for the subject, where the DfE publishes it, and leaves the loan
at subject level.

## Why all graduates for the subject figures, but women and men for the calibration?

The DfE's forecast is for all borrowers, and women and men have different pay
paths, so the model is tuned on the two separately and weighted. For a
subject's own figures, LEO publishes quartiles for all its graduates together,
and using them means the tool's slider, the table and the chart of subjects all
say the same thing. Taking the subject figures from the simulation instead put
them up to five years away from the slider's middle (materials and
technology: 31 years against 36).

## Why give graduates not in work no earnings?

LEO counts the share of graduates not in sustained work or study five years
out, and the quartiles of pay are for those who are. The lowest places are
given nothing so that the median place is the median graduate. It is harsh on
that group, whose real earnings are low rather than zero, and it is one reason
the model's bottom tenth repays less than the DfE's.

## Why the DfE's average balance for everyone?

It is the balance the DfE's own forecast uses, so the comparison with it is
like for like. A reader with a bigger balance, from a four-year course or a
larger maintenance loan, will take longer to clear it if they clear it at all,
and will have more written off if they do not.

## Why 2024-25 prices, and why start from the DfE's ratio?

Because that is how the DfE reports real terms, and the first version of this
got it wrong by assuming an inflation path. Taking the DfE's own ratio of real
to nominal balance at the start of repayment, then 2% a year after, puts the
model's real figures on the same footing as the forecast it is checked against.

## Why the type 1 percentile?

Because it is the one that reproduces the DfE's published ranges. The
interpolated percentile most software uses by default gets two of the eight
numbers wrong, which is how I found out which one the DfE used.

## Why only graduates with the same A-level points for the attainment check?

Comparing subjects among graduates in one band of prior attainment (300 to 359
UCAS points) is the cleanest test the published data allows of whether the pay
gap between subjects is really a gap in who studies them. It is not a causal
estimate: graduates with the same grades still chose different subjects for
reasons that may also affect their pay.

## Why no charting library?

The charts are a line, a dot plot and a band. Drawn as SVG directly they
resize to the screen so their text stays readable on a phone, take their
colours from CSS so a change of theme needs no redraw, and keep the page under
60 KB of JavaScript.
