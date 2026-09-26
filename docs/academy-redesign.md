# Academy refresh

The Academy now has 21 bilingual mini-courses, including exactly 7 new Beginner,
3 Essential and 2 Advanced courses. Each addition has three lessons and three
questions with explanations. Existing course identifiers and session progress remain compatible.

New Beginner courses: investment planning, compounding, funds, order execution,
financial statements, inflation and investor psychology.
New Essential courses: allocation/correlation, earnings quality and bonds/duration.
New Advanced courses: valuation scenarios and backtest robustness.

The Academy gets its own university/open-book emblem, a blue/violet hero,
locally rendered course illustrations, searchable catalog, new/in-progress/completed
filters, guided paths, weekly study planning and a progress tab. The illustration
assets are original vector artwork with no external image requests.

Seven offline labs: compounding, purchasing power, two-asset allocation,
trade expectancy, duration sensitivity, growing-perpetuity sensitivity and a
downloadable decision journal. Assumptions and omitted factors are shown alongside
results. Study minutes are estimates. Progress is session-only, not a permanent account.
Quiz completion requires at least 80%; unanswered submissions do not complete a course.

## Validation

- Four content/art/formula tests, including zero and negative returns, correlation
  extremes and invalid perpetuity assumptions.
- Streamlit AppTest: 21-card catalog, search empty state, 12-new filter,
  all seven labs in English and Arabic, and all twelve new course final lessons,
  quiz submissions and completed state.
- Additional guards checked for unanswered and unsuccessful quizzes and invalid
  discount/growth combinations.
- All changed Python files compile; all generated illustrations parse as XML.
- Full browser layout/keyboard verification remains pending: the local cloud-browser
  preview connection timed out. The included image is explicitly a static design
  excerpt using the actual logo and cover artwork, not a screenshot of deployment.

Run from the repository root after installing requirements:

    python -m unittest discover -s tests -v

## Further reading

- https://www.investor.gov/introduction-investing
- https://www.investor.gov/introduction-investing/getting-started/asset-allocation
- https://www.finra.org/investors/investing/investment-products/bonds

Examples and calculations are original educational exercises, not recommendations.
