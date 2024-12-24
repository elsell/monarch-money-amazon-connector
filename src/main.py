"""
Monarch Money Amazon Connector

Copyright (C) 2024 github.com/elsell

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import toml
from .config.types import Config
from .cli import MonarchMoneyAmazonConnectorCLI
from asyncio import run
from loguru import logger
import sys

logger.remove()
logger.add(
    sink=sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Monarch Money Amazon Connector")
    parser.add_argument(
        "--config",
        type=str,
        default="mmac.toml",
        help="Path to the configuration file",
    )
    return parser.parse_args()


def parse_toml(toml_path: str) -> Config:
    """
    Parse the toml file at the given path and return the dictionary.
    """
    with open(toml_path, "r") as f:
        print(toml.load(f))
        f.seek(0)
        return Config.model_validate(toml.load(f))


def get_config(args: argparse.Namespace) -> Config:
    toml_config = parse_toml(args.config)
    return toml_config


def main():
    args = parse_args()

    config = get_config(args)

    cli = MonarchMoneyAmazonConnectorCLI(config=config)

    try:
        run(cli.annotate_transactions())
    except KeyboardInterrupt:
        logger.info("Aborting.")
        return


if __name__ == "__main__":
    main()
