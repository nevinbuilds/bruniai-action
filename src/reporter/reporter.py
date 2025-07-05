import logging
import aiohttp
from typing import Optional, Dict, Any, List
from .types import MultiPageReportData

logger = logging.getLogger(__name__)

class BruniReporter:
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url
        logger.info(f"Bruni reporter initialized with endpoint: {api_url}")

    async def send_multi_page_report(self, multi_page_report: MultiPageReportData) -> Optional[Dict[str, Any]]:
        """
        Send a multi-page report to the Bruni API using aiohttp.

        Args:
            multi_page_report: The multi-page report data to send

        Returns:
            The API response data if successful, None otherwise

        Raises:
            aiohttp.ClientError: If there's an error making the request
            ValueError: If the response status is not successful
        """
        if not self.token:
            logger.info("No Bruni token provided, skipping multi-page report submission")
            return None

        logger.info(f"Sending multi-page report to Bruni API with {len(multi_page_report['reports'])} pages...")

        logger.debug(f"Multi-page report JSON: {multi_page_report}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.api_url,
                    json=multi_page_report,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.token}"
                    }
                ) as response:
                    if not response.ok:
                        response_text = await response.text()
                        logger.error(f"API Error: {response.status} - {response_text}")
                        raise ValueError(
                            f"Failed to send multi-page report: {response.status} - {response_text}"
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
                logger.error(f"Error sending multi-page report to Bruni API: {e}")
                raise
