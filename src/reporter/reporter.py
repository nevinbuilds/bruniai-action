import logging
import aiohttp
from typing import Optional, Dict, Any
from .types import ReportData, ImageReferences

logger = logging.getLogger(__name__)

class BruniReporter:
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url
        logger.info(f"Bruni reporter initialized with endpoint: {api_url}")

    async def send_report(self, report: ReportData) -> Optional[Dict[str, Any]]:
        """
        Send a report to the Bruni API using aiohttp.

        Args:
            report: The report data to send

        Returns:
            The API response data if successful, None otherwise

        Raises:
            aiohttp.ClientError: If there's an error making the request
            ValueError: If the response status is not successful
        """
        if not self.token:
            logger.info("No Bruni token provided, skipping report submission")
            return None

        logger.info(f"Sending report to Bruni API...")

        logger.debug(f"Report JSON: {report}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    json=report,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}"
                    }
                ) as response:
                    if not response.ok:
                        response_text = await response.text()
                        logger.error(f"API Error: {response.status} - {response_text}")
                        raise ValueError(
                            f"Failed to send report: {response.status} - {response_text}"
                        )

                    # Try to parse the response as JSON first
                    try:
                        response_data = await response.json()
                        logger.info(f"API Response ({response.status}): {response_data}")
                        return response_data
                    except:
                        # If response is not JSON, fall back to text
                        response_text = await response.text()
                        logger.info(f"API Response ({response.status}): {response_text}")
                        return {"message": response_text}

            except aiohttp.ClientError as e:
                logger.error(f"Error sending report to Bruni API: {e}")
                raise
