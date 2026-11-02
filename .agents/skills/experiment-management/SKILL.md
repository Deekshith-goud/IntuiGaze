---
name: experiment-management
description: Design reproducible model experiments, maintain baseline comparisons, record configurations and artifacts, and prevent test-set overfitting.
---

# Experiment management

Each experiment must include:
- Hypothesis and intended improvement.
- Data version and split manifest/hash.
- Model family, input/target contract and preprocessing version.
- Seed, runtime/dependency environment, configuration and code commit.
- Training budget, early-stopping rule and checkpoint selection rule.
- Baseline metrics measured on identical partitions.
- Validation metrics, test protocol, runtime/memory metrics and group-level error analysis.
- Artifact path/checksum, decision and limitations.

Start from the simplest appropriate baseline. Use validation data for all iteration and tune no decision against the final test set. For large datasets, begin with a bounded pipeline smoke test then scale by shards/batches. Never use training loss alone as the model-selection metric.
