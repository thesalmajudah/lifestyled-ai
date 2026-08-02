# Retrieval Evaluation

k = 5

## Summary

| Mode | Avg Hit Rate@k | Avg Relevance@k |
|---|---:|---:|
| vector | 0.8 | 0.6333 |
| hybrid | 0.8 | 0.6333 |

## Per-query Results

| Query ID | Mode | Hit@k | Relevance@k | Predicted IDs | Expected IDs |
|---|---|---:|---:|---|---|
| Q001 | vector | 1.0 | 0.5 | P001 ,P005 ,P010 ,P008 ,P017 | P002 ,P006 ,P010 ,P017 |
| Q002 | vector | 0.0 | 0.0 | P005 ,P006 ,P010 ,P008 ,P017 | P003 ,P015 |
| Q003 | vector | 1.0 | 1.0 | P018 ,P007 ,P009 ,P005 ,P015 | P009 ,P018 ,P007 |
| Q004 | vector | 1.0 | 1.0 | P020 | P020 |
| Q005 | vector | 1.0 | 0.6667 | P016 ,P001 ,P007 ,P008 ,P004 | P001 ,P016 ,P019 |
| Q001 | hybrid | 1.0 | 0.5 | P001 ,P005 ,P010 ,P008 ,P017 | P002 ,P006 ,P010 ,P017 |
| Q002 | hybrid | 0.0 | 0.0 | P006 ,P005 ,P010 ,P008 ,P017 | P003 ,P015 |
| Q003 | hybrid | 1.0 | 1.0 | P018 ,P009 ,P005 ,P007 ,P015 | P009 ,P018 ,P007 |
| Q004 | hybrid | 1.0 | 1.0 | P020 | P020 |
| Q005 | hybrid | 1.0 | 0.6667 | P001 ,P016 ,P007 ,P008 ,P004 | P001 ,P016 ,P019 |