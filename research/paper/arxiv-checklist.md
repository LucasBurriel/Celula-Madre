# arXiv Submission Checklist — Célula Madre

## Metadata
- **Title:** Célula Madre: Evolutionary Optimization of LLM Agent Prompts Through Selection Pressure
- **Authors:** Tesla & Lucas Burriel (Independent Research)
- **Contact:** teslaburriel@gmail.com
- **Categories:** cs.CL (primary), cs.AI, cs.NE (secondary)
- **License:** CC-BY 4.0

## Pre-submission
- [x] Paper compiles cleanly (pdflatex, 7 pages, no errors)
- [x] All 3 figures generated and included
- [x] Table 1 with V6 results
- [x] Algorithm 1 pseudocode
- [x] 11 references with proper arxiv IDs
- [x] natbib bibliography
- [ ] **Add V6.5 market selection results** (TASK-029 in progress)
- [ ] **Consider adding V7 PoC results** (blocked on compute)
- [ ] Proofread one final time
- [ ] Verify all arxiv IDs resolve correctly
- [ ] Check figure quality at print resolution

## Content Review Notes (2026-02-12)
1. **Static baseline estimated (~79%)** — acknowledged in Limitations. Acceptable.
2. **V7 described as "in progress"** — update Section 6 with V6.5 results when available.
3. **Single LLM limitation** — noted. Could strengthen with one Claude/GPT run but not blocking.
4. **Abstract is strong** — 3 clear contributions, quantitative results.
5. **Discussion well-structured** — 4 hypotheses for null result, Austrian economics connection.

## Submission Steps
1. Wait for V6.5 results (market selection on AG News) — adds V7's key innovation to the data
2. Update paper with V6.5 findings (new table, figure, discussion subsection)
3. Final proofread
4. Create .tar.gz with: celula-madre.tex, figures/, .bbl
5. Submit to arxiv.org under cs.CL
6. Cross-list to cs.AI and cs.NE

## Decision
**Hold submission until V6.5 completes.** Market selection results will significantly strengthen the paper by testing the Austrian economics thesis (currently only theoretical). Expected: 1-2 days.
