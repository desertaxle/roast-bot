# Roast Bot

My personal automated shame machine that scrapes my contributions to [Prefect](https://github.com/PrefectHQ/prefect) and roasts me in the [Prefect dev log](https://dev-log.prefect.io) when I forget to write a post.

## What it does

This bot watches for recent blog posts in the [PrefectHQ dev-log repo](https://github.com/PrefectHQ/dev-log). If I haven't written anything in the past week, it:

1. Finds my merged PRs from the past week
2. Picks the most embarrassing one
3. Uses Claude to write a scathing blog post roasting my code
4. Commits it to the dev log repo which is automatically published

Because nothing motivates consistent blogging quite like the threat of AI-generated public humiliation.
