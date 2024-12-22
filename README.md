# Monarch Money Amazon Connector (MMAC)

Monarch Money Amazon Connector automatically adds
a note to each Amazon transaction in Monarch Money containing
the list of items ordered.

Why?

To make it easier to categorize Amazon transactions, eliminating
the need to go order-by-order to find the matching transaction
in your Amazon Account.


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
```

### Run MMAC

```bash
mmac
```
