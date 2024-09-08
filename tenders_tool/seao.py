import pandas as pd
from pandas import json_normalize
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import copy
import requests
from datetime import datetime

class GithubSEAO:
    """Utility class to retrieve github info and links"""

    def __init__(
        self,
        owner="poivronjaune",
        repository="dataset_seao",
        branch="main",
        latest_only=True,
        auto_load=True,
        verbose=True,
    ) -> None:
        if owner is None or owner == "" or not isinstance(owner, str):
            raise ValueError("Invalid owner parameter.")
        if repository is None or repository == "" or not isinstance(repository, str):
            raise ValueError("Invalid repository parameter.")
        if branch is None or branch == "" or not isinstance(branch, str):
            raise ValueError("Invalid branch parameter.")

        self.identifiant = "d23b2e02-085d-43e5-9e6e-e1d558ebfdd5"
        self.owner = owner
        self.repo = repository
        self.branch = branch
        self.files = None
        self.json_data = None
        self.json_scheama = self.init_json_schema()
        self.latest_only = latest_only
        self.verbose = verbose
        
        # Timer storage to calculate loading time
        self.start_load = None
        self.end_load = None
        self.loading_time = None
        if auto_load:
            self.auto_load_data()

    def auto_load_data(self):
        self.get_list_from_github_repo()
        self.load_seao_data()

    def __str__(self) -> str:
        # url = f'{self.owner} -> {self.repo} -> {self.branch}'
        url = f"Data source: https://github.com/{self.owner}/{self.repo}/tree/{self.branch} \n"
        size = f"Dataset size: {len(self.json_data)} \n"
        json_type = f"Type for data: {type(self.json_data)} \n"
        item_type = f"Type for item: {type(self.json_data[0])} \n"
        item_keys = f"item root keys: {self.json_data[0].keys()} \n"

        result_str = url + size + json_type + item_type + item_keys
        return result_str

    @property
    def api_content(self) -> str:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/"
        return url

    def repo_content(self, folder="/") -> list:
        """Return a list of files from  github repo that start_with a specifc string"""
        if (
            folder == "/"
            or folder == ""
            or folder is None
            or not isinstance(folder, str)
        ):
            folder = ""
        url = self.api_content + folder
        content = requests.get(url, timeout=10)
        list_of_json_objects = content.json()
        return list_of_json_objects

    def get_list_from_github_repo(self):
        json_list = self.repo_content()
        file_urls = [
            record["download_url"] for record in json_list if record["type"] == "file"
        ]
        self.files = file_urls
        return file_urls

    def load_json_from_url(self, url):
        """Utility function to load a singe json from a raw github url"""
        try:
            # Fetch the JSON file from the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses (e.g., 404, 500)

            # Parse the JSON content
            json_data = response.json()
            return json_data

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return None

    def load_seao_data(self):
        """Load all seao files available from raw github files repo"""
        self.start_load = None
        self.end_load = None
        self.loading_time = None

        if self.files is None:
            raise ValueError(
                "No raw github files available for downloading. Use GitHubSEAO.get_list_from_github_repo first"
            )

        sub_files = self.files
        if self.latest_only:
            sub_files = sub_files[-1:]
        self.start_load = datetime.now()
        if self.verbose:
            print(f"Starttime for loading: {self.start_load}")

        self.json_data = []
        for idx, file_url in enumerate(sub_files):
            if self.verbose:
                print(f"{idx+1:02d}/{len(sub_files):03d}  --> Loading file: {file_url}")
            try:
                published_info = self.load_json_from_url(file_url)
                # Extract 'releases' data and append it to the list
                releases = published_info.get("releases", [])
                self.json_data.extend(releases)

            except Exception as e:
                print(f"Error loading file {file_url}: {e}")

        self.end_load = datetime.now()
        self.loading_time = self.end_load - self.start_load
        loading_min = self.loading_time.total_seconds() / 60
        if self.verbose:
            print(f"Endtime for loading:   {self.end_load}")
            print(f"Loading time: {loading_min} minutes")

    def init_json_schema(self):
        self.json_schema = {
            "$schema": "https://json-schema.org/draft/2020-12",
            "$id": "https://www.donneesquebec.ca/recherche/dataset/systeme-electronique-dappel-doffres-seao",
            "title": "seao",
            "description": "SEAO Open Data Schema proposal",
            "properties": {
                "ocid": {"type": "string"},
                "id": {"type": "string"},
                "date": {"type": "string"},
                "language": {"type": "string"},
                "tag": {"$ref": "#/definitions/tag_object"},
                "initiationType": {"type": "string"},
                "tender": {"type": "object"},
                "parties": {"type": "array"},
            },
            "required": ["ocid", "id", "date", "language", "parties"],
            "additionalProperties": True,
            "definitions": {
                "tag_object": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "award",
                            "awardUpdate",
                            "awardCancellation",
                            "contract",
                            "contractTermination",
                            "contractUpdate",
                            "tender",
                            "tenderCancellation",
                            "tenderUpdate",
                        ],
                    },
                    "minItems": 1,
                    "maxItems": 3,
                }
            },
        }

    def validate_json_format(self, go_validate=False):
        """Schema validation of items. Loops through all items. Very long to run"""
        if go_validate:
            try:
                for record in self.json_data:
                    validate(instance=record, schema=self.json_schema)
                if self.verbose:
                    print("Validation passed")
            except ValidationError as e:
                if self.verbose:
                    print(f"Validation failed, {e}")
