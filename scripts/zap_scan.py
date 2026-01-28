#!/usr/bin/env python3
"""
OWASP ZAP security testing script for the News Sentiment Comparison API.

This script runs basic security scans against the API using OWASP ZAP.
It performs spider crawling and active vulnerability scanning.

Prerequisites:
- ZAP must be running (see README for setup instructions)
- Or use Docker: docker run -d -p 8080:8080 zaproxy/zap-stable zap.sh -daemon -host 0.0.0.0 -port 8080

Usage:
    python scripts/zap_scan.py --target http://localhost:8000
    python scripts/zap_scan.py --target https://your-api.onrender.com --api-key YOUR_KEY
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from zapv2 import ZAPv2
except ImportError:
    print("Error: zapv2 not installed. Install with: pip install python-owasp-zap-v2.4")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ZAPScanner:
    """OWASP ZAP scanner wrapper for API security testing."""

    def __init__(self, zap_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """
        Initialize ZAP scanner.

        Args:
            zap_url: URL where ZAP is running (default: http://localhost:8080)
            api_key: ZAP API key (optional, but recommended for production)
        """
        self.zap_url = zap_url
        self.api_key = api_key or os.getenv("ZAP_API_KEY")
        self.zap = ZAPv2(proxies={"http": zap_url, "https": zap_url}, apikey=self.api_key)
        self.target_url: Optional[str] = None

    def wait_for_zap(self, timeout: int = 30) -> bool:
        """Wait for ZAP to be ready."""
        logger.info(f"Waiting for ZAP to be ready at {self.zap_url}...")
        start_time = time.time()
        last_error = None
        while time.time() - start_time < timeout:
            try:
                version = self.zap.core.version
                logger.info(f"ZAP version: {version}")
                return True
            except Exception as e:
                last_error = str(e)
                logger.debug(f"ZAP not ready yet: {e}")
                time.sleep(2)
        logger.error(f"ZAP did not become ready in time")
        logger.error(f"Last error: {last_error}")
        logger.error(f"Tried connecting to: {self.zap_url}")
        logger.error("\nTroubleshooting:")
        logger.error("1. If using ZAP GUI: Enable API in Tools → Options → API")
        logger.error("2. If using Docker: docker run -d -p 8080:8080 zaproxy/zap-stable zap.sh -daemon")
        logger.error("3. Check if ZAP is running: Check the ZAP GUI or 'docker ps' for Docker")
        logger.error("4. Try a different port: --zap-url http://localhost:8090 (if ZAP is on port 8090)")
        return False

    def spider_scan(self, target_url: str, max_children: int = 10) -> str:
        """
        Run a spider scan to discover URLs.

        Args:
            target_url: Target URL to scan
            max_children: Maximum number of children to crawl

        Returns:
            Scan ID
        """
        logger.info(f"Starting spider scan of {target_url}")
        self.target_url = target_url

        # Set up context (optional, but helps ZAP understand the app)
        context_name = "news-sentiment-api"
        try:
            context_id = self.zap.context.new_context(context_name)
            self.zap.context.include_in_context(context_name, f"{target_url}.*")
        except Exception as e:
            logger.warning(f"Could not create context: {e}")

        # Start spider scan
        scan_id = self.zap.spider.scan(
            url=target_url,
            maxchildren=max_children,
            recurse=True
        )

        # Wait for spider to complete
        logger.info("Spider scan started, waiting for completion...")
        while int(self.zap.spider.status(scan_id)) < 100:
            progress = int(self.zap.spider.status(scan_id))
            logger.info(f"Spider progress: {progress}%")
            time.sleep(2)

        logger.info("Spider scan completed")
        return scan_id

    def active_scan(self, target_url: str) -> str:
        """
        Run an active vulnerability scan.

        Args:
            target_url: Target URL to scan

        Returns:
            Scan ID
        """
        logger.info(f"Starting active scan of {target_url}")
        self.target_url = target_url

        # Start active scan
        scan_id = self.zap.ascan.scan(url=target_url, recurse=True, inscopeonly=True)

        # Wait for scan to complete
        logger.info("Active scan started, waiting for completion...")
        while int(self.zap.ascan.status(scan_id)) < 100:
            progress = int(self.zap.ascan.status(scan_id))
            logger.info(f"Active scan progress: {progress}%")
            time.sleep(5)

        logger.info("Active scan completed")
        return scan_id

    def get_alerts(self, risk_level: Optional[str] = None) -> list:
        """
        Get security alerts from ZAP.

        Args:
            risk_level: Filter by risk level (High, Medium, Low, Informational)

        Returns:
            List of alerts
        """
        alerts = self.zap.core.alerts(baseurl=self.target_url)
        if risk_level:
            alerts = [a for a in alerts if a.get("risk") == risk_level]
        return alerts

    def generate_report(self, output_file: str, report_format: str = "JSON") -> str:
        """
        Generate a security report.

        Args:
            output_file: Path to output file
            report_format: Report format (JSON, HTML, XML, MD)

        Returns:
            Path to generated report
        """
        logger.info(f"Generating {report_format} report: {output_file}")

        if report_format.upper() == "JSON":
            alerts = self.get_alerts()
            report_data = {
                "target": self.target_url,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "alerts": alerts,
                "summary": self._generate_summary(alerts)
            }
            with open(output_file, "w") as f:
                json.dump(report_data, f, indent=2)
        elif report_format.upper() == "HTML":
            report_html = self.zap.core.htmlreport()
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_html)
        elif report_format.upper() == "XML":
            report_xml = self.zap.core.xmlreport()
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_xml)
        elif report_format.upper() == "MD":
            report_md = self.zap.core.mdreport()
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_md)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

        logger.info(f"Report saved to {output_file}")
        return output_file

    def _generate_summary(self, alerts: list) -> dict:
        """Generate a summary of alerts by risk level."""
        summary = {
            "High": 0,
            "Medium": 0,
            "Low": 0,
            "Informational": 0,
            "Total": len(alerts)
        }
        for alert in alerts:
            risk = alert.get("risk", "Informational")
            if risk in summary:
                summary[risk] += 1
        return summary

    def print_summary(self):
        """Print a summary of findings to console."""
        alerts = self.get_alerts()
        summary = self._generate_summary(alerts)

        print("\n" + "=" * 60)
        print("ZAP Security Scan Summary")
        print("=" * 60)
        print(f"Target: {self.target_url}")
        print(f"\nAlerts by Risk Level:")
        print(f"  High:           {summary['High']}")
        print(f"  Medium:         {summary['Medium']}")
        print(f"  Low:            {summary['Low']}")
        print(f"  Informational:  {summary['Informational']}")
        print(f"  Total:          {summary['Total']}")

        if summary['High'] > 0 or summary['Medium'] > 0:
            print("\n⚠️  High/Medium risk alerts found:")
            for alert in alerts:
                risk = alert.get("risk", "Informational")
                if risk in ["High", "Medium"]:
                    print(f"\n  [{risk}] {alert.get('name', 'Unknown')}")
                    print(f"    URL: {alert.get('url', 'N/A')}")
                    print(f"    Description: {alert.get('description', 'N/A')[:100]}...")

        print("=" * 60 + "\n")
        return summary

    def should_fail_on_risk_levels(self, risk_levels: list[str]) -> bool:
        """
        Check if scan should fail based on specified risk levels.
        
        Args:
            risk_levels: List of risk levels to check (e.g., ["High", "Medium"])
            
        Returns:
            True if any of the specified risk levels have findings > 0
        """
        alerts = self.get_alerts()
        summary = self._generate_summary(alerts)
        
        for risk_level in risk_levels:
            if summary.get(risk_level, 0) > 0:
                return True
        return False


def main():
    """Main entry point for ZAP scanning script."""
    parser = argparse.ArgumentParser(
        description="Run OWASP ZAP security scans against the News Sentiment API"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target API URL (e.g., http://localhost:8000 or https://api.onrender.com)"
    )
    parser.add_argument(
        "--zap-url",
        default="http://localhost:8080",
        help="ZAP API URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--api-key",
        help="ZAP API key (or set ZAP_API_KEY env var)"
    )
    parser.add_argument(
        "--skip-spider",
        action="store_true",
        help="Skip spider scan (only run active scan)"
    )
    parser.add_argument(
        "--skip-active",
        action="store_true",
        help="Skip active scan (only run spider scan)"
    )
    parser.add_argument(
        "--report-format",
        choices=["JSON", "HTML", "XML", "MD"],
        default="JSON",
        help="Report format (default: JSON)"
    )
    parser.add_argument(
        "--output-dir",
        default="zap-reports",
        help="Output directory for reports (default: zap-reports)"
    )
    parser.add_argument(
        "--fail-on",
        help="Comma-separated list of risk levels that should cause exit code 1 (e.g., 'high,medium'). "
             "If any of these risk levels have findings > 0, the script will exit with code 1. "
             "Valid values: High, Medium, Low, Informational. "
             "Useful for CI/CD pipelines to fail on security findings."
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Initialize scanner
    scanner = ZAPScanner(zap_url=args.zap_url, api_key=args.api_key)

    # Wait for ZAP to be ready
    if not scanner.wait_for_zap():
        logger.error("ZAP is not available. Make sure ZAP is running.")
        logger.info("Start ZAP with: docker run -d -p 8080:8080 zaproxy/zap-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config 'api.addrs.addr.name=.*' -config 'api.addrs.addr.regex=true'")
        sys.exit(1)

    try:
        # Run spider scan
        if not args.skip_spider:
            scanner.spider_scan(args.target)
        else:
            logger.info("Skipping spider scan")

        # Run active scan
        if not args.skip_active:
            scanner.active_scan(args.target)
        else:
            logger.info("Skipping active scan")

        # Generate and save report
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"zap_report_{timestamp}.{args.report_format.lower()}"
        scanner.generate_report(str(report_file), args.report_format)

        # Print summary and get summary data
        summary = scanner.print_summary()

        logger.info(f"Scan complete. Report saved to {report_file}")

        # Check if we should fail based on --fail-on argument
        if args.fail_on:
            risk_levels = [r.strip().capitalize() for r in args.fail_on.split(",")]
            # Validate risk levels
            valid_levels = {"High", "Medium", "Low", "Informational"}
            invalid_levels = [r for r in risk_levels if r not in valid_levels]
            if invalid_levels:
                logger.error(f"Invalid risk levels in --fail-on: {invalid_levels}. Valid values: High, Medium, Low, Informational")
                sys.exit(1)
            
            if scanner.should_fail_on_risk_levels(risk_levels):
                logger.error(f"Scan found security issues at risk levels: {', '.join(risk_levels)}. Failing as requested.")
                sys.exit(1)
            else:
                logger.info(f"No findings at risk levels: {', '.join(risk_levels)}. Scan passed.")

    except KeyboardInterrupt:
        logger.warning("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
