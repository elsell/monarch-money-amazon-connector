# Monarch Money Amazon Connector (MMAC)

Monarch Money Amazon Connector automatically adds
a note to each Amazon transaction in [Monarch Money](https://monarchmoney.com) containing
the list of items ordered.

Why?

To make it easier to categorize Amazon transactions, eliminating
the need to go order-by-order to find the matching transaction
in your Amazon Account.

Under the hood, MMAC uses the [`monarchmoney`](https://github.com/hammem/monarchmoney) python package.

> [!Warning]
>
> **⚠️ MMAC IS IN ALPHA**
>
> I'm making this repo public early to solicit feedback on the functionality,
> and to provide opportunities for collaboration.
>
> No warranty is provided, and the documentation is incomplete at this point.
>
> **If you're just looking for something that works, check back in a few months :)**

## Screenshot

The description and the tags were automatically inserted by MMAC!

![image](https://github.com/user-attachments/assets/9efbeccf-d186-4ca4-aef4-6d4915e9afc5)


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

## A Note About SemVer

MMAC is committed to using [Semantic Versioning](https://semver.org/) for its codebase.
This means we are going to increment major versions relatively quickly, as strictly adhering to SemVer requires
a major version increment for every breaking change.

There is a lot of discussion about whether, for this reason, SemVer is "bad". In my opinion,
SemVer *is* bad, but only for user-facing application versions.

Why?

Technical breaking changes (changes that break backwards compatibility in the codebase, but do not
change the user experience/release a feature) are essential to track for the developer. However,
the user of an application would be forgiven if they were confused when their app bumped from
v1.0.0 to v2.0.0 without any notable changes.

So, what's the solution?

I don't know. Maintaining two versions is messy and complicated, a hybrid concatenation
of SemVer and AppVer is also messy and potentially confusing to the user, and choosing one or
the other is an imperfect solution. Please - let me know if you've figured this out!

As for MMAC, we're going to stick to SemVer. Let's face it: If you're popping open your terminal
to `pip install` this package, you can handle reading the release notes to figure out what's new
between v1.0.0 and v2.0.0.

You're smart, I'm lazy. Let's just use SemVer.

## Thanks!

This project wouldn't be possible without the community [`Monarch Money Library`](https://github.com/hammem/monarchmoney)!
Head over there and give that project some love!
