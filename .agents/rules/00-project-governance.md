# Project governance rules

Apply to every task.

- Start with repository archaeology: inspect source, tests, configs, `git status`, and the nearest documentation before drafting changes.
- Use evidence-based scope. Do not do broad rewrites, speculative abstractions, or “cleanup” unrelated to the requested outcome.
- Before editing, outline the issue, likely root cause, proposed files, acceptance criteria, and test plan. For very small changes, this can be a short checklist.
- If the task requires an unknown fact (dataset labels, camera geometry, intended use, hardware budget, or deployment target), mark it unknown and design an inspection step. Do not silently pick values.
- Preserve public APIs unless a change is explicitly intended. If an API changes, update call sites and docs in the same change.
- Avoid duplicate helpers, overlapping skills, parallel configuration sources, and multiple versions of the same instructions. Update the canonical source and link to it.
- Do not overwrite existing config or documentation without comparing its current contents.
- End with a factual summary: changed files, checks actually run, results, limitations, and whether the change is safe to merge.
