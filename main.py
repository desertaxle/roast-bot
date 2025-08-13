from pathlib import Path
import re
import tempfile
import time
from typing import Any
from prefect import flow, get_run_logger, task
import anyio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
import textwrap

import toml

DEV_LOG_REPO_URL = "https://github.com/PrefectHQ/dev-log.git"
_FRONT_MATTER_RE = re.compile(r"^\ufeff?\+\+\+\s*\n(.*?)\n\+\+\+\s*(?:\n|$)", re.DOTALL)


@task
async def set_up_git():
    # check token works
    await anyio.run_process(["gh", "auth", "status"], check=True)
    # set up git credential manager
    await anyio.run_process(["gh", "auth", "setup-git"], check=True)


@task(retries=3, retry_delay_seconds=5)
async def clone_dev_log(tmp_dir: Path) -> None:
    logger = get_run_logger()
    logger.info(f"Cloning dev log to {tmp_dir}")
    await anyio.run_process(["git", "clone", DEV_LOG_REPO_URL, tmp_dir], check=True)
    logger.info("Dev log successfully cloned")


@task
async def any_recent_blog_posts(handle: str, tmp_dir: Path) -> bool:
    """
    Check if any blog posts were written in the past week.
    """
    logger = get_run_logger()
    logger.info(f"Checking for recent entries for {handle} in {tmp_dir}")
    for entry in (tmp_dir / "content" / "blog").glob("*.md"):
        if entry.stat().st_mtime > time.time() - 7 * 24 * 60 * 60:
            meta = parse_frontmatter(await anyio.Path(entry).read_text())
            if (
                meta.get("draft", False)
                and meta.get("params", {}).get("authorGitHubHandle", "") == handle
            ):
                return True
    return False


@task(retries=3, retry_delay_seconds=5)
async def generate_roast(handle: str, tmp_dir: Path) -> None:
    logger = get_run_logger()
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a blog post writer. You write blog posts about Python software development.",
            allowed_tools=["Bash", "Read", "WebSearch", "Write"],
            cwd=tmp_dir,
        )
    ) as client:
        # Send the query
        await client.query(
            textwrap.dedent(
                f"""
                Write a blog post roasting my ({handle}) contributions to the PrefectHQ/prefect repo in the past week. 

                To accomplish this:
                1. Find ALL my merged PRs in the PrefectHQ/prefect repo in the past week.
                2. Read the description and diff of each PR.
                3. Pick the most interesting PR.
                4. If the PR closes an issue, read the issue for more context
                5. Write a blog post roasting the chosen PR.

                When you're done, write the blog post to a markdown file in @content/blog and prefix the filename with "roast-".

                Things to keep in mind:
                - Use the `gh` CLI for all GitHub operations.
                - Mention that the reason you're doing this is because I was too lazy to write a dev log entry this week.
                - Be sure to include links to PRs and commits in the blog post.
                - Include the frontmatter for the blog post matching the format of other blog posts in @content/blog.
                    - Set the author as "roast-bot".
                    - `draft = false`
                    - Add a "roast" tag to the blog post.
                - Take a look at other roast blog posts in @content/blog to avoid repeating yourself.
                """
            )
        )

        # Stream the response
        async for message in client.receive_response():
            if content := getattr(message, "content", None):
                # Print streaming content as it arrives
                for block in content:
                    if text := getattr(block, "text", None):
                        logger.info(text)


@task(retries=3, retry_delay_seconds=5)
async def push_to_dev_log(handle: str, tmp_dir: Path) -> None:
    logger = get_run_logger()
    logger.info("Pushing roast to dev log")

    await anyio.run_process(["git", "add", "."], check=True, cwd=tmp_dir)
    await anyio.run_process(
        ["git", "commit", "-m", f"Update dev log with roast of {handle}"],
        check=True,
        cwd=tmp_dir,
    )
    await anyio.run_process(["git", "push"], check=True, cwd=tmp_dir)
    logger.info("Pushed roast to dev log")


def parse_frontmatter(content: str) -> dict[str, Any]:
    """
    Parse the frontmatter from a markdown file.
    """
    m = _FRONT_MATTER_RE.match(content)
    if not m:
        return {}
    raw = m.group(1)
    meta = toml.loads(raw)

    return meta


@flow
async def roast_prefect_developer(handle: str):
    logger = get_run_logger()

    await set_up_git()

    with tempfile.TemporaryDirectory(delete=False) as temp_dir:
        tmp_path = Path(temp_dir)
        await clone_dev_log(tmp_path)
        if not await any_recent_blog_posts(handle, tmp_path):
            logger.info(f"No recent blog posts found for {handle}. Time to roast!")
            await generate_roast(handle, tmp_path)
            await push_to_dev_log(handle, tmp_path)
        else:
            logger.info(f"Recent blog posts found. I'll get you next time, {handle}!")


if __name__ == "__main__":
    anyio.run(roast_prefect_developer, "desertaxle")
