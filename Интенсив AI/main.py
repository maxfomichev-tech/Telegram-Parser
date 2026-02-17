import argparse
import sys

from gigachat import OpenRouterError, generate_summary
from utils import choose_input, get_logger

logger = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI-инструмент для выжимки текста с помощью OpenRouter."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary = subparsers.add_parser("summary", help="Сделать краткую выжимку текста.")
    summary.add_argument("--file", type=str, help="Путь к файлу с текстом.")
    summary.add_argument("--text", type=str, help="Текст напрямую.")
    return parser


def handle_summary(args: argparse.Namespace) -> int:
    try:
        user_text = choose_input(args.text, args.file)
    except Exception as exc:  # noqa: BLE001
        logger.error("%s", exc)
        return 1

    try:
        summary_text = generate_summary(user_text)
    except OpenRouterError as exc:
        logger.error("Ошибка API: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.error("Неожиданная ошибка: %s", exc)
        return 1

    print("Краткая выжимка:\n")
    print(summary_text)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "summary":
        return handle_summary(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

