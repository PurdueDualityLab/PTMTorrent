from ModelHubClass import ModelHubClass
from huggingface_hub import HfApi, snapshot_download
from huggingface_hub.hf_api import ModelInfo, DatasetInfo
import shutil
from sys import argv

import logging
import petl as etl
from petl import Table
from collections import OrderedDict

SCRATCH_DIR = "/scratch/bell/jone2078"
CACHE_DIR = f"{SCRATCH_DIR}/huggingface_cache"
DATA_DIR = f"{SCRATCH_DIR}/huggingface_data"
# HuggingFace extends ModelHubClass in order to provide a class base for the HuggingFace API
class HuggingFace(ModelHubClass):
    api: HfApi = HfApi()
    models: Table
    datasets: Table

    # model_constraints and dataset_constraints provide the tests
    # that are run on the model and dataset metadata obtained from
    # the HF API to ensure that the metadata is valid
    model_constraints : list[dict] = [
        dict(name="modelId exists", field="modelId", test=str),
        dict(name="sha exists", field="sha", test=str),
        dict(name="lastModified exists", field="lastModified", test=str),
        dict(name="tags exists", field="tags", test=list),
        dict(name="pipeline_tag exists", field="pipeline_tag", test=bool),
        dict(name="siblings exists", field="siblings", test=list),
        dict(name="private exists", field="private", test=bool),
        dict(name="author exists", field="author", test=str),
        dict(name="config exists", field="config", test=dict),
        dict(name="securityStatus exists", field="securityStatus", test=str),
        dict(name="_id exists", field="_id", test=str),
        dict(name="id exists", field="id", test=str),
        dict(name="cardData exists", field="cardData", test=dict),
        dict(name="likes exists", field="likes", test=int),
        dict(name="downloads exists", field="downloads", test=int),
        dict(name="library_name exists", field="library_name", test=str),
        dict(name="modelId and id are equivalent", test=lambda row: row["modelId"] == row["id"]),
    ]

    dataset_constraints : list[dict] = [
        dict(name="id exists", field="id", test=str),
        dict(name="sha exists", field="sha", test=str),
        dict(name="lastModified exists", field="lastModified", test=str),
        dict(name="tags exists", field="tags", test=list),
        dict(name="private exists", field="private", test=bool),
        dict(name="author exists", field="author", test=str),
        dict(name="description exists", field="description", test=str),
        dict(name="citation exists", field="citation", test=str),
        dict(name="cardData exists", field="cardData", test=dict),
        dict(name="siblings exists", field="siblings", test=list),
        dict(name="_id exists", field="_id", test=str),
        dict(name="disabled exists", field="disabled", test=bool),
        dict(name="gated exists", field="gated", test=bool),
        dict(name="likes exists", field="likes", test=int),
        dict(name="downloads exists", field="downloads", test=int),
        dict(name="paperswithcode_id exists", field="paperswithcode_id", test=str),
    ]

    # model_headers and dataset_headers provide the headers for the
    # model and dataset metadata tables
    model_headers : tuple = (
        "modelId",
        "sha",
        "lastModified",
        "tags",
        "pipeline_tag",
        "siblings",
        "private",
        "author",
        "config",
        "securityStatus",
        "_id",
        "id",
        "cardData",
        "likes",
        "downloads",
        "library_name",
    )

    dataset_headers : tuple = (
        "id",
        "sha",
        "lastModified",
        "tags",
        "private",
        "author",
        "description",
        "citation",
        "cardData",
        "siblings",
        "_id",
        "disabled",
        "gated",
        "likes",
        "downloads",
        "paperswithcode_id",
    )


    def __init__(self):
        self.name = "HuggingFace"
        self.data_path = "/scratch/bell/jone2078/PTMTorrent/ptm_torrent/huggingface/data"
        self.transformed_data = {}        
        self.transformed_data["model_hub"] = etl.fromcolumns([['url', 'name'],
                                              ['https://huggingface.co/models', 'HuggingFace']])


    def extract(self, amount: int|None = 1000):
        raw_models: list[ModelInfo] = self.api.list_models(limit=amount,
                                                           full=True,
                                                           cardData=True,
                                                           fetch_config=True,
                                                           sort="downloads",
                                                           direction=-1)
        dict_models = []
        model: self.api.ModelInfo
        for model in raw_models:
            model = model.__dict__
            model["siblings"] = [sibling.__dict__ for sibling in model["siblings"]
                                 if "config" in sibling.rfilename and "json" in sibling.rfilename]
            dict_models.append(model)

        self.models = etl.fromdicts(dict_models)
        logging.warning(f"Found {etl.nrows(self.models)} models on HuggingFace API")
        logging.warning(f"Found {etl.nrows(self.models.select(lambda row: row['downloads'] >= 10**6))} models on HuggingFace API")
        logging.warning(f"Model Headers: {etl.header(self.models)}")

        raw_datasets: list[DatasetInfo] = self.api.list_datasets(limit=amount,
                                                                 full=True,
                                                                 sort="downloads",
                                                                 direction=-1)
        dict_datasets = [dataset.__dict__ for dataset in raw_datasets]

        for dataset in dict_datasets:
            dataset["siblings"] = [sibling.__dict__ for sibling in dataset["siblings"]
                                 if "config" in sibling.rfilename and "json" in sibling.rfilename] \
                                 if dataset["siblings"] else None

        self.datasets = etl.fromdicts(dict_datasets)
        logging.warning(f"Found {etl.nrows(self.datasets)} datasets on HuggingFace API")
        logging.warning(f"Dataset Headers: {etl.header(self.datasets)}")

    def verify_extraction(self):
        problems = etl.validate(self.models, constraints = self.model_constraints, header = self.model_headers)
        logging.warning(f"Total {self.name} model Errors: {problems.nrows()}")
        logging.debug(f"{self.name} model Errors:\n{problems.lookall()}")

        problems = etl.validate(self.datasets, constraints = self.dataset_constraints, header = self.dataset_headers)
        logging.warning(f"Total {self.name} dataset Errors: {problems.nrows()}")
        logging.debug(f"{self.name} dataset Errors:\n{problems.lookall()}")

    def downloadZipSnapshot(self, model_id: str, repo_type: str, zip: bool) -> str | None:
        destination_dir = f'{self.data_path}/{repo_type}/{model_id}'
        try:
            snapshot_dir = snapshot_download(model_id,
                                    repo_type=repo_type,
                                    cache_dir=CACHE_DIR,
                                    local_dir=f"{DATA_DIR}/{model_id}",
                                    local_dir_use_symlinks=False)
            snapshot_zip = shutil.make_archive(destination_dir, 'zip', snapshot_dir) if zip else snapshot_dir
        except Exception as e:
            print(f"An Exception occurred: {e}")
            snapshot_zip = e
        return snapshot_zip


    # Obtains relevant data from the extracted data through transformations
    # Should result in self.transformed_data having the tables created within DB_Schema.sql
    def transform(self, min_download: int = 1, max_download: int = 10**9):
        self.model_transform(min_download, max_download)
        self.dataset_transform(min_download, max_download)

    def model_transform(self, min_download: int = 1, max_download: int = 10**9):
        self.models = self.models.progress(50000, prefix="Unpacking CardData: ").unpackdict('cardData')
        self.models = self.models.progress(50000, prefix="Unpacking Config: ").unpackdict('config')
        self.models = self.models.progress(50000, prefix="Melting: ").melt('_id')
        self.models = self.models.progress(500000, prefix="Recasting: ").recast()
        self.models = self.models.progress(50000, prefix="Sorting: ").sort('downloads', reverse=True)

        model_mapping = OrderedDict()
        hf_tags = self.api.get_model_tags()
        model_mapping['context_id'] = 'modelId'
        model_mapping['sha'] = 'sha'
        model_mapping['lastModified'] = 'lastModified'
        model_mapping['tags'] = lambda row: set([tag for tag in row['tags']
                                             if ":" not in tag and
                                                tag not in hf_tags.dataset.values() and
                                                tag not in hf_tags.language.values() and
                                                tag not in hf_tags.library.values() and 
                                                tag not in hf_tags.license.values()] + ([row['pipeline_tag']] or []))
        model_mapping['author'] = 'author'
        model_mapping['citation'] = 'citation'
        model_mapping['architectures'] = 'architectures'
        model_mapping['framework'] = 'model_type'
        model_mapping['library'] = 'library_name'
        model_mapping['likes'] = 'likes'
        model_mapping['downloads'] = 'downloads'
        model_mapping['repo_url'] = lambda row: f"https://huggingface.co/{row['modelId']}"
        model_mapping['datasets'] = 'datasets'
        model_mapping['language'] = 'language'
        model_mapping['license'] = 'license'
        model_mapping['config_file'] = 'siblings'
        model_mapping['paper'] = lambda row: [f"https://arxiv.org/abs/{tag.replace('arxiv:','')}" for tag in row['tags'] if 'arxiv:' in tag] or None
        model_mapping['original_data'] = lambda row: row
        snapshots = {}
        commits = {}
        for row in self.models.dicts():
            logging.warning(f"{row['modelId']}: ")

            if row['downloads'] >= min_download and row['downloads'] < max_download:
                snapshots[row['modelId']] = self.downloadZipSnapshot(row['modelId'], 'model', False)
                try:
                    commit_info = self.api.list_repo_commits(row['modelId'])
                    gitref_info = self.api.list_repo_refs(row['modelId'])
                    commits[row['modelId']] = {"commits": commit_info, "gitrefs": gitref_info}
                except:
                    commits[row['modelId']] = None
            else:
                snapshots[row['modelId']] = "Out of download range"
                commits[row['modelId']] = None

            logging.warning(snapshots[row['modelId']])


        model_mapping['snapshot'] = lambda row: snapshots[row['modelId']] or None
        model_mapping['commit_info'] = lambda row: commits[row['modelId']] or None

        self.transformed_data["model"] = self.models.progress(10000, prefix="Mapping: ").fieldmap(model_mapping)

        # self.transformed_data["model_to_tag"] = self.transformed_data["model"].cut('context_id', 'tags')
        # self.transformed_data["model_to_language"] = self.transformed_data["model"].cut('context_id', 'language')
        # self.transformed_data["model_to_paper"] = self.transformed_data["model"].cut('context_id', 'paper')
        # self.transformed_data["model_to_license"] = self.transformed_data["model"].cut('context_id', 'license')
        # self.transformed_data["model_to_author"] = self.transformed_data["model"].cut('context_id', 'author')
        # self.transformed_data["model_to_framework"] = self.transformed_data["model"].cut('context_id', 'framework')
        # self.transformed_data["model_to_architecture"] = self.transformed_data["model"].cut('context_id', 'architectures')
        # self.transformed_data["model_to_library"] = self.transformed_data["model"].cut('context_id', 'library')
        # self.transformed_data["model_to_config_file"] = self.transformed_data["model"].cut('context_id', 'config_file')
        # self.transformed_data["model_to_dataset"] = self.transformed_data["model"].cut('context_id', 'datasets')

    def dataset_transform(self, min_download: int = 1, max_download: int = 10**9):
        self.datasets = self.datasets.unpackdict('cardData')
        self.datasets = self.datasets.sort('downloads', reverse=True)

        dataset_mapping = OrderedDict()
        dataset_mapping['context_id'] = 'id'
        dataset_mapping['sha'] = 'sha'
        dataset_mapping['lastModified'] = 'lastModified'
        dataset_mapping['tags'] = lambda row: set([tag for tag in row['tags']
                                             if ":" not in tag and tag not in hf_tags.language.values()] + \
                                            (row['task_categories'] if row['task_categories'] else []) + \
                                            (row['size_categories'] if row['size_categories'] else []) + \
                                            (row['annotations_creators'] if row['annotations_creators'] else []) + \
                                            (row['language_creators'] if row['language_creators'] else []) + \
                                            (row['annotation_creators'] if row['annotation_creators'] else []))
        dataset_mapping['author'] = 'author'
        dataset_mapping['description'] = 'description'
        dataset_mapping['citation'] = 'citation'
        dataset_mapping['likes'] = 'likes'
        dataset_mapping['downloads'] = 'downloads'
        dataset_mapping['type'] = 'type'
        dataset_mapping['paperswithcode_id'] = 'paperswithcode_id'
        dataset_mapping['repo_url'] = lambda row: f"https://huggingface.co/datasets/{row['id']}"
        dataset_mapping['source'] = 'source_datasets'
        dataset_mapping['language'] = lambda row: (row['language'] if row['language'] else []) + \
                                                  (row['multilinguality'] if row['multilinguality'] else []) \
                                                  if row['language'] or row['multilinguality'] else None
        dataset_mapping['license'] = 'license'
        dataset_mapping['dataset_info'] = 'dataset_info'
        dataset_mapping['paper'] = lambda row: [f"https://arxiv.org/abs/{tag.replace('arxiv:','')}"
                                              for tag in row['tags'] if 'arxiv:' in tag] or None
        dataset_mapping['original_data'] = lambda row: row
        snapshots = {}
        commits = {}
        for row in self.datasets.dicts():
            logging.warning(row['id'])
            if row['downloads'] >= min_download and row['downloads'] < max_download:
                snapshots[row['id']] = self.downloadZipSnapshot(row['id'], 'dataset', False)
                try:
                    commit_info = self.api.list_repo_commits(row['id'], repo_type='datasets')
                    gitref_info = self.api.list_repo_refs(row['id'], repo_type='datasets')
                    commits[row['id']] = {"commits": commit_info, "gitrefs": gitref_info}
                except:
                    commits[row['id']] = None
            else:
                snapshots[row['id']] = "Out of download range"
                commits[row['id']] = None

        dataset_mapping['snapshot'] = lambda row: snapshots[row['id']] or None
        dataset_mapping['commit_info'] = lambda row: commits[row['id']] or None

        self.transformed_data["dataset"] = self.datasets.fieldmap(dataset_mapping)
        logging.warning(self.transformed_data["dataset"].header())

        # self.transformed_data["dataset_to_language"] = self.transformed_data["dataset"].cut('context_id', 'language')
        # self.transformed_data["dataset_to_paper"] = self.transformed_data["dataset"].cut('context_id', 'paper')
        # self.transformed_data["dataset_to_license"] = self.transformed_data["dataset"].cut('context_id', 'license')
        # self.transformed_data["dataset_to_author"] = self.transformed_data["dataset"].cut('context_id', 'author')
        # self.transformed_data["dataset_to_license"] = self.transformed_data["dataset"].cut('context_id', 'license')
        # self.transformed_data["dataset_to_tags"] = self.transformed_data["dataset"].cut('context_id', 'tags')
        # self.transformed_data["dataset_to_info"] = self.transformed_data["dataset"].cut('context_id', 'dataset_info')

if __name__ == "__main__":
    min = eval(argv[1])
    if len(argv) > 2:
        max = eval(argv[2])
    else:
        max = 10**9
    logging.basicConfig(level=logging.WARNING)
    hf = HuggingFace()
    hf.extract(amount=None)
    hf.model_transform(min_download=min, max_download=max)
    hf.load(f"{min}-{max}")