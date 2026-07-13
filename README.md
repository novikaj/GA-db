# Growth Analytics Take-Home

An interview-ready growth analytics project combining a reproducible dbt transformation layer, source data, Python analysis, and stakeholder-ready outputs.

## Project structure

- `seeds/` — supplied paid-media, CRM, and product-usage CSV data loaded by dbt
- `models/staging/` — typed, cleaned source models
- `models/marts/` — campaign-level growth metrics
- `analysis.py` — complementary analysis and slide-generation script
- `outputs/` — generated analysis tables and presentation artifacts

## Run the dbt project

1. Install dbt with the BigQuery adapter (`pip install dbt-bigquery`).
2. Copy `profiles.yml.example` to `~/.dbt/profiles.yml` and supply your GCP project ID.
3. Authenticate with `gcloud auth application-default login` if using OAuth.
4. From this directory, run:

   ```bash
   dbt seed
   dbt build
   dbt docs generate
   ```

`fct_campaign_performance` joins paid spend to CRM leads and closed-won revenue by `campaign_id`. Cost and return metrics should be treated as directional: the campaign taxonomy has known inconsistencies and the product-event window is longer than the paid/CRM window.

## Share with interviewers

The repository intentionally excludes local credentials and dbt build artifacts. Before sharing, review `git status`, commit the source and models, then add the remote repository URL:

```bash
git add .
git commit -m "Initial growth analytics take-home"
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```
