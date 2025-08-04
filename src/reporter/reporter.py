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

        # Split the reports into smaller chunks if necessary
        max_chunk_size = 1000000  # 1 MB, adjust as needed
        reports = multi_page_report['reports']
        chunks = [reports[i:i + max_chunk_size] for i in range(0, len(reports), max_chunk_size)]

        all_responses = []

        async with aiohttp.ClientSession() as session:
            for chunk in chunks:
                logger.info(f"Sending chunk with {len(chunk)} pages to Bruni API...")
                try:
                    async with session.post(
                        self.api_url,
                        json={"reports": chunk, "test_data": multi_page_report['test_data']},
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
                            all_responses.append(response_data)
                        except:
                            # If response is not JSON, fall back to text
                            response_text = await response.text()
                            logger.info(f"API Response ({response.status}): {response_text}")
                            all_responses.append({"message": response_text})

                except aiohttp.ClientError as e:
                    logger.error(f"Error sending multi-page report to Bruni API: {e}")
                    raise

        return all_responses
