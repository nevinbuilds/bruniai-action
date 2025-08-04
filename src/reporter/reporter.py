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
        max_chunk_size = 1  # 1 report per chunk to avoid large payloads
        reports = multi_page_report['reports']
        chunks = [reports[i:i + max_chunk_size] for i in range(0, len(reports), max_chunk_size)]

        all_responses = []
        test_id = None  # Will be set after first chunk

        async with aiohttp.ClientSession() as session:
            for chunk_index, chunk in enumerate(chunks):
                logger.info(f"Sending chunk {chunk_index + 1}/{len(chunks)} with {len(chunk)} pages to Bruni API...")

                # Prepare payload
                payload = {
                    "reports": chunk,
                    "test_data": multi_page_report['test_data'],
                    "chunk_index": chunk_index,
                    "total_chunks": len(chunks)
                }

                # Add test_id for subsequent chunks
                if test_id is not None:
                    payload["test_id"] = test_id

                try:
                    async with session.post(
                        self.api_url,
                        json=payload,
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

                            # Extract test_id from first chunk response
                            if chunk_index == 0 and test_id is None:
                                test_id = response_data.get('test').get('id')
                                if test_id:
                                    logger.info(f"Extracted test_id: {test_id}")
                        except:
                            # If response is not JSON, fall back to text
                            response_text = await response.text()
                            logger.info(f"API Response ({response.status}): {response_text}")
                            all_responses.append({"message": response_text})

                except aiohttp.ClientError as e:
                    logger.error(f"Error sending multi-page report to Bruni API: {e}")
                    raise

        return all_responses

