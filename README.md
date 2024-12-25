# Monarch Money Amazon Connector (MMAC)

Monarch Money Amazon Connector automatically adds
a note to each Amazon transaction in Monarch Money containing
the list of items ordered.

Why?

To make it easier to categorize Amazon transactions, eliminating
the need to go order-by-order to find the matching transaction
in your Amazon Account.

Under the hood, MMAC uses the [`monarchmoney`](https://github.com/hammem/monarchmoney) python package.

> [!Warning]
>
> **MMAC IS IN ALPHA**
>
> I'm making this repo public early to solicit feedback on the functionality,
> and to provide opportunities for collaboration.
>
> No warranty is provided, and the documentation is incomplete at this point.
>
> **If you're just looking for something that works, check back in a few months :)**


## Quick Start

### Install MMAC using pip:

```bash
pip install monarch-money-amazon-connector
```

### Create Configuration File

Create a file called `mmac.toml`. This file
will contain configuration values needed to run MMAC.

```toml
# mmac.toml

# Replace with your Monarch account credentials.
monarch_account.email = "example@example.com"
monarch_account.password = "password"


# Your amazon account credentials
[[amazon_accounts]]
email = "test@example.com"
password = "password"

# (Optional): If you have multiple amazon accounts,
# you can define them by duplicating the first section
# with the additional credentials.
# [[amazon_accounts]]
# email = "test2@example.com"
# password = "password"

# (Optional): Use the OpenAI API to *attempt* to
# auto solve captcha images. This is NOT very reliable,
# but may work with simpler captchas.
[llm]
# Whether to use the LLM captcha solver
enable_llm_captcha_solver = true
# Your OpenAI API Key
api_key = "sk-********"
# (Optional): The OpenAI Project ID
# project = "proj_**********"

# (Optional): Specify whether to show the browser
# window while scraping, or now (headless).
# headless = true
```

### Run MMAC

```bash
mmac
```
