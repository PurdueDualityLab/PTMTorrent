from torch import hub
from ModelHubClass import ModelHubClass
from typing import List
from gql import gql, Client, transport
from gql.transport.aiohttp import AIOHTTPTransport
from queries import LICENSE_QUERY, FILE_QUERY, GITHUB_TOKEN

import petl as etl
from petl import Table
import logging
import json
from collections import OrderedDict

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url="https://api.github.com/graphql", 
                             headers={"Authorization": GITHUB_TOKEN,
                                      "Accept": "application/vnd.github.hawkgirl-preview+json"})

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

class PyTorch(ModelHubClass):
    api: hub = hub
    models: Table

    model_headers : tuple = (
        "layout",
        "background-class",
        "body-class",
        "category",
        "title",
        "summary",
        "image",
        "author",
        "tags",
        "github-link",
        "github-id",
        "featured_image_1",
        "featured_image_2",
        "accelerator",
        "demo-model-link",
        'order',
    )

    model_constraints : List[dict] = [
        dict(name="layout exists", field="layout", test=str),
        dict(name="background-class exists", field="background-class", test=str),
        dict(name="body-class exists", field="body-class", test=str),
        dict(name="category exists", field="category", test=str),
        dict(name="title exists", field="title", test=str),
        dict(name="summary exists", field="summary", test=str),
        dict(name="image exists", field="image", test=str),
        dict(name="author exists", field="author", test=str),
        dict(name="tags exists", field="tags", test=str),
        dict(name="github-link exists", field="github-link", test=str),
        dict(name="github-id exists", field="github-id", test=str),
        dict(name="featured_image_1 exists", field="featured_image_1", test=str),
        dict(name="featured_image_2 exists", field="featured_image_2", test=str),
        dict(name="accelerator exists", field="accelerator", test=str),
        dict(name="demo-model-link exists", field="demo-model-link", test=str),
    ]

    def __init__(self):
        self.name = "PyTorch"
        self.transformed_data = {}
        self.transformed_data["model_hub"] = etl.fromcolumns([['url', 'name'],
                                              ['https://github.com/onnx/models', self.name]])

    def extract(self):
        variables = {
        "owner": "pytorch",
        "name": "hub"
        }
        query = gql(FILE_QUERY)

        files = client.execute(query, variable_values=variables)
        markdown_files = [{
                     "name": file["name"],
                     "text": file["object"]["text"],
                     "size": file["object"]["byteSize"]
                     }
                     for file in files["repository"]["object"]["entries"]
                     if ".md" in file["name"]]
        
        model_dicts = []
        for file in markdown_files:
            if("CODE_OF_CONDUCT" in file["name"] or
               "CONTRIBUTING" in file["name"] or
               "README" in file["name"]):
                continue
            info = file["text"].split("---")[1].strip().split("\n")
            model_info = {i.split(': ')[0]: i.split(': ')[1].strip()
                          for i in info}
            model_dicts.append(model_info)

        self.models = etl.fromdicts(model_dicts)
        logging.info(f"Extracted {etl.nrows(self.models)} models from PyTorch")
        logging.debug(f"PyTorch headers: {etl.header(self.models)}")

    def verify_extraction(self):
        problems = etl.validate(self.models, constraints = self.model_constraints, header = self.model_headers)
        logging.info(f"Total {self.name} models with problems: {problems.nrows()}")
        logging.debug(f"{self.name} model Errors:\n{problems.lookall()}")

    def transform(self):
        variables = {
            "owner": "",
            "name": "",
        }
        query = gql(LICENSE_QUERY)

        license_rows = []
        for row in etl.dicts(self.models):
            variables["owner"] = row["github-id"].split("/")[0]
            variables["name"] = row["github-id"].split("/")[1]
            result = client.execute(query, variable_values=variables)
            license = result["repository"]["licenseInfo"]["key"] if result["repository"]["licenseInfo"] else None
            license_rows.append(license)

        self.models = etl.addcolumn(self.models, "license", license_rows)

        model_mapping = OrderedDict()
        model_mapping["context_id"] = "title"
        model_mapping["repo_url"] = "github-link"
        model_mapping["library"] = lambda row: "pytorch"
        model_mapping["tags"] = lambda row: [word.strip() for word in row['tags'].replace('[','').replace(']','').split(',')]
        model_mapping["author"] = "author"
        model_mapping["license"] = "license"

        self.transformed_data["model"] = etl.fieldmap(self.models, model_mapping)

        self.transformed_data["model_to_library"] = self.transformed_data["model"].cut('context_id', 'library')
        self.transformed_data["model_to_tag"] = self.transformed_data["model"].cut('context_id', 'tags')
        self.transformed_data["model_to_license"] = self.transformed_data["model"].cut('context_id', 'license')
        self.transformed_data["model_to_author"] = self.transformed_data["model"].cut('context_id', 'author')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pt = PyTorch()
    pt.extract()
    pt.transform()
    pt.frequency(pt.transformed_data["model"])
