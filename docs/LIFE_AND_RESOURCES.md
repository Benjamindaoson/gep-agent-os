# Multi-goal planning and resource checks

GEP manages a *person*, not only a Git repository:

```bash
gep goal-add --name "Complete OMSCS" --domain learning
gep goal-add --name "Maintain health and rest" --domain life
gep life-plan GOAL_ID --priority 1 --weekly-hours 10 --protected
gep goal-link HEALTH_ID CAREER_ID --relation supports
gep life-report
```

The budget check warns of an overcommitted week. Protected goals remain
first-class constraints. All hours and relationships are user-declared; no
speculative life scores.

Real read-only resource checks:

```bash
gep provider-check --provider github --resource owner/repository
# Set VERCEL_TOKEN through secure environment configuration:
gep provider-check --provider vercel --resource your-project-id
gep provider-check --provider huggingface --resource org/dataset
```

No cloud instance is provisioned, no deployment is triggered and no GPU is
rented by these commands. They let users validate external resource
identities as part of a portable recovery plan.
