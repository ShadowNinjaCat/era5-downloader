import argparse
import os
import json
import time
import cdsapi
from cdsapi.api import Result

from core.utils.logger import Logger

def era5_download(enqueued_file: str, poll_interval: int = 60):
    with open(enqueued_file, 'r') as f:
        enqueued = json.load(f)
    client = cdsapi.Client()
    session = client.session
    for item in enqueued:
        reply = item.get('reply', {})
        output_file = item['output_file']

        if os.path.exists(output_file):
            Logger.info(f"Already downloaded: {output_file}")
            continue

        asset_href = reply.get('asset', {}).get('value', {}).get('href')

        if asset_href:
            Logger.info(f"Asset ready for {output_file}, downloading directly via session...")
            try:
                response = session.get(asset_href, stream=True)
                response.raise_for_status()
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                continue
            except Exception as e:
                Logger.error(f"Direct download failed for {output_file}: {e}")
                continue

        request_id = reply.get('request_id')
        if not request_id:
            Logger.warning(f"No asset href or request_id for {output_file}, skipping")
            continue

        result = Result(client, reply)
        while True:
            result.update()
            status = result.status
            Logger.info(f"Status for {request_id} ({output_file}): {status}")
            if status == 'completed':
                result.download(output_file)
                Logger.info(f"Downloaded {output_file}")
                break
            elif status in ['failed', 'deleted']:
                Logger.error(f"Failed for {request_id}: {status}")
                break
            time.sleep(poll_interval)

def main():
    parser = argparse.ArgumentParser(description="Monitor and download enqueued ERA5 requests")
    parser.add_argument('--request-json', type=str, default='requests.json', help='JSON file with enqueued info')
    parser.add_argument('--poll-interval', type=int, default=60, help='Polling interval in seconds')
    args = parser.parse_args()

    Logger.info("Starting ERA5 download process")
    try:
        era5_download(args.request_json, args.poll_interval)
        Logger.info("Download process completed")
    except Exception as e:
        Logger.error(f"Error in download: {e}")

if __name__ == "__main__":
    main()
