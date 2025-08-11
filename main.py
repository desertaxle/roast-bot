from prefect import flow, get_run_logger, task
import anyio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
import textwrap


@task
async def generate_roast(handle: str) -> None:
    logger = get_run_logger()
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a blog post writer. You write blog posts about Python software development.",
            allowed_tools=["Bash", "Read", "WebSearch", "Write"],
        )
    ) as client:
        # Send the query
        await client.query(
            textwrap.dedent(
                f"""
                Write a blog post roasting my ({handle}) contributions to the PrefectHQ/prefect repo in the past week. 

                To accomplish this:
                1. Find all my merged PRs in the PrefectHQ/prefect repo in the past week.
                2. Read the description and diff of each PR.
                3. Pick the most interesting PR.
                4. If the PR closes an issue, read the issue for more context
                5. Write a blog post roasting the chosen PR.

                When you're done, write the blog post to a file called "blog_post.md" in the current directory.

                Things to keep in mind:
                - Mention that the reason you're doing this is because I was too lazy to write a dev log entry this week.
                - Be sure to include links to PRs and commits in the blog post.
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


@flow
async def roast_prefect_developer(handle: str):
    await generate_roast(handle)


if __name__ == "__main__":
    anyio.run(roast_prefect_developer, "desertaxle")
