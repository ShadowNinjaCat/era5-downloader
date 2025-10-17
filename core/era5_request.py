import argparse
import cdsapi
import os
import json
import yaml
from copy import deepcopy
from typing import List, Dict, Any

from utils.logger import Logger

class ERA5Request:
    @staticmethod
    def era5_requests(config_path: str, base_output_filename: str = "atmospheric") -> List[Dict[str, Any]]:
        config = ERA5Request._load_config(config_path)
        dataset = config['dataset']
        base_request = config['request']
        years = base_request.pop('year', [])
        file_format = base_request.get('format', 'grib')
        save_folder = config.get('save_path', 'data')
        os.makedirs(save_folder, exist_ok=True)

        if not years:
            Logger.warning("No years specified in config 'request.year'. Nothing to request.")
            return []

        client = cdsapi.Client()
        enqueued = []

        for year in years:
            output_file =  f"{save_folder}/{base_output_filename}_{year}.{file_format}"
            Logger.info(f"Requesting data {dataset} for year {year}")
            request = deepcopy(base_request)
            request['year'] = str(year)

            result = client.retrieve(dataset, request, target=None)
            reply_dict = result.json

            enqueued.append({
                'reply': reply_dict,
                'location': result.location,
                'output_file': output_file
            })

        return enqueued

    @staticmethod
    def _load_config(config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            Logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(config_path)
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        required_keys = ['dataset', 'request']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required key in config: {key}")
        Logger.info(f"Config loaded from {config_path}")
        return config

def main():
    parser = argparse.ArgumentParser(description="ERA5 requests to CDS")
    parser.add_argument('--config', type=str, default='config/era5_request.yaml', help='Path to YAML config')
    parser.add_argument('--base-filename', type=str, default='atmospheric', help='Base output filename')
    parser.add_argument('--output-json', type=str, default='requests.json', help='JSON file to save enqueued info')
    args = parser.parse_args()
    Logger.info("Starting ERA5 request process")
    try:
        requests = ERA5Request.era5_requests(args.config,  args.base_filename)
        with open(args.output_json, 'w') as f:
            json.dump(requests, f, indent=4)
        Logger.info(f"{len(requests)} requests, saved to {args.output_json}")
    except Exception as e:
        Logger.error(f"Error in request: {e}")

if __name__ == "__main__":
    main()
