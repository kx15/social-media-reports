"""Main entry point for the automated social media reporting tool."""
from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta

from utils.helpers import get_logger

logger = get_logger(__name__)
logging.basicConfig(level=logging.INFO)


def _previous_month() -> tuple[int, int]:
    """Return (year, month) for the month prior to today."""
    today = date.today()
    first_of_current = date(today.year, today.month, 1)
    last_month = first_of_current - timedelta(days=1)
    return last_month.year, last_month.month


def run_report() -> None:
    """Run the full reporting pipeline for the previous month."""
    from processors import aggregator
    from reporters import excel_report, pdf_report
    from notifiers import email_sender
    from dashboards import google_sheets

    year, month = _previous_month()
    month_label = date(year, month, 1).strftime("%B %Y")
    logger.info("Starting social media report for %s", month_label)

    # 1. Collect & store metrics
    all_metrics = aggregator.run(year, month)

    # 2. Generate reports
    excel_path = excel_report.generate(year, month, all_metrics)
    pdf_path = pdf_report.generate(year, month, all_metrics)

    # 3. Push to Google Sheets
    google_sheets.push(year, month, all_metrics)

    # 4. Send email notification
    subject = f"Social Media Monthly Report – {month_label}"
    body = (
        f"Please find the automated social media report for {month_label} attached.\n\n"
        "This report was generated automatically by the monthly reporting pipeline."
    )
    email_sender.send(subject, body, [excel_path, pdf_path])

    logger.info("Report pipeline complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated Social Media Reporting Tool")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the report pipeline once and exit (used by GitHub Actions).",
    )
    args = parser.parse_args()

    if args.run_once:
        run_report()
    else:
        # Local scheduled mode: run at 08:00 on the 1st of every month.
        try:
            import schedule
        except ImportError:
            logger.error("'schedule' package not installed. Run: pip install schedule")
            raise

        import time

        def _job() -> None:
            if date.today().day == 1:
                run_report()

        schedule.every().day.at("08:00").do(_job)
        logger.info("Scheduler started – report will run at 08:00 on the 1st of each month.")
        logger.info("Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(60)


if __name__ == "__main__":
    main()
