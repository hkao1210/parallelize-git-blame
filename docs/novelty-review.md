# Prior-art review — 2026-11-18

## Finding

The broad idea of parallel Git blame is **not novel**. A narrower contribution
combining exact Git-compatible edge summaries with demand-driven speculative
windows remains **unestablished**, not verified novel. A finite web search cannot
prove the absence of equivalent work, unpublished implementations, or patents.
The current dense index/terminal representation and function substitution are
standard techniques; associativity alone is not a sufficient research novelty.

## Primary sources examined

1. Matheus Tavares Bernardino, [Improving Parallelism on Git, 2019 proposal](https://matheustavares.dev/assets/tavares-capstone-project-proposal.pdf),
   pp. 1–3: explicitly proposes threading git-blame and thread-safe object-store
   access. This directly precedes the broad proposal here. His
   [final essay, January 2020](https://matheustavares.dev/assets/tavares-final-essay.pdf)
   instead reports git-grep work; p. 6 treats blame parallelization as future work.
   Do not misreport the proposal as a completed parallel-blame speedup.
2. Gote, Scholtes, Schweitzer, [git2net, MSR 2019](https://www.sg.ethz.ch/publications/2019/gote2019git2net---an/gote2019git2net.pdf),
   pp. 5–6: distributes co-edit extraction across independent commits, using
   blame for attribution. This is repository-mining parallelism across queries,
   not evidence of a parallel prefix algorithm for one single-file blame query.
3. [Mercurial fastannotate import, 2018](https://lists.mercurial-scm.org/pipermail/mercurial-devel/2018-August/269341.html):
   implements cached annotation with a linelog representation. Attribution
   preprocessing and cached history are therefore established related ideas.
   Its warm-cache gains are not evidence of uncached, all-costs-included Git
   speedup or exact Git attribution semantics.
4. [Git's file-history internals, Derrick Stolee, 2022](https://github.blog/open-source/git/gits-database-internals-iii-file-history-queries/):
   documents demand-driven blame and changed-path Bloom filters. Important
   baseline optimizations already exist; eager edge processing must overcome
   work that native Git avoids. No new performance numbers from this article
   are treated as measurements of our machine.
5. [gitoxide January 2025 implementation report](https://github.com/GitoxideLabs/gitoxide/discussions/1791):
   describes experimental blame, performance improvements in progress, and
   ambiguous alignment (the slider problem). This is a relevant alternative
   implementation; the report is historical and not a current benchmark.
6. [grit-lib blame API](https://docs.rs/grit-lib/latest/grit_lib/blame/index.html):
   exposes per-new-line origin mapping and a history walker. This is direct
   prior art for decomposing matching into line correspondence. The moving
   `latest` URL does not establish an implementation date or parallel scan.
7. [Git's 2014 blame performance rewrite](https://github.com/git/git/commit/7e6ac6e4391caa0fc379cb699013d503380e4214)
   is an additional implementation-history lead. The web view did not expose
   enough patch detail to evaluate its algorithm in this review.

## Search coverage and limits

Queries included: `git blame parallel algorithm prefix scan performance`,
`git blame parallel implementation gitoxide blame`, `site.lore.kernel.org/git
blame parallel threads performance`, `"parallel git blame"`, `"git-blame"
"threading" Tavares patch`, `"blame" "speculative" git`, `"blame" "line mapping"
parallel`, `"git blame" "precompute" performance`, `"git2net" "parallel" commits`,
and `"fastannotate" mercurial cache blame`. Checked scholarly PDFs, author
reports, implementation documentation, and mailing-list material. Search engine
results for Git-hosted files contain many irrelevant uses of the UI word blame.
No directly matching bounded speculative prefix implementation was identified
in the inspected sources. That is a limited negative search result, not a proof.
The PMC article endpoint returned a bot challenge; the authors' PDF was used
instead. A comprehensive Git mailing-list patch audit and citation-forward
review of annotation algorithms have not been completed.

## Defensible contribution if experiments justify it

An empirical study of when exact single-file Git provenance can profit from
bounded speculative parallel edge processing, including negative cases, work
amplification, and measured scheduling/object-store overhead. A stronger novel
algorithm claim requires a compact representation or scheduling result that
materially differs from this prior art, plus a wider literature review. The
current implementation should be presented as an experiment, not a first-ever
parallel blame algorithm.
