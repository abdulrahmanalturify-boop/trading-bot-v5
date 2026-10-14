# Academy microlearning refresh — 14 October 2026

The academy now opens with a clear start/continue action, three short starter paths, and three featured mini-courses. The catalog has search, level/status/reading-time filters and nine-card pagination. Study materials combine expandable notes, downloadable Markdown summaries, flashcards and the existing videos.

Added 12 bilingual beginner courses (about four minutes of reading each), with three lessons, immediate practice questions and a final three-question quiz. Seven of the new courses also embed a calculator or portfolio lab. There are now 37 courses, including 26 beginner courses. Five new offline calculators bring the lab hub to 12 exercises.

New topics: price versus value, total return, loss recovery, bid–ask spread, limit orders, market capitalization and splits, dividends, fees, currency returns, rebalancing, scam warning signs, and evaluating news.

Existing IDs and lessons are retained. Progress now uses URL-safe encoded, versioned stable IDs compatible with the existing browser storage allowlist. Old index codes migrate using a frozen 25-course mapping, so inserting beginner courses cannot shift saved progress to another course. Lesson steps are bounded on load. Final-quiz feedback is tied to the submitted answers. Selected starter paths retain their own next-course sequence.

Validation: Python compilation; nine unittest/AppTest tests covering bilingual lessons, all new quizzes and completion, all 12 labs, materials, catalog filtering/pagination, financial calculations and legacy progress migration. Browser installation was unavailable in this environment, so visual desktop/mobile inspection and deployed-browser persistence still need verification. Responsive academy-scoped styles are included; other site pages are unchanged.

The new content uses hypothetical examples and links to official Investor.gov educational references. Reading-time labels do not include optional practice, quiz or external-video time.
