import ast
import re
import json
import petl as etl
# Create a visitor class to traverse the AST and extract required information
# class HubLoadVisitor(ast.NodeVisitor):
#     def __init__(self):
#         self.pairs = []
    
#     def visit_Call(self, node):
#         if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute):
#             if (
#                 node.func.value.attr == 'hub'
#                 and node.func.value.value.id == 'torch'
#                 and node.func.attr == 'load'
#             ):
#                 args = node.args
#                 if len(args) >= 2:
#                     repo_or_dir = args[0]
#                     model = args[1]
#                     self.pairs.append((repo_or_dir, model))
        
#         self.generic_visit(node)

# Visitor class to traverse the AST and extract relevant information
class HubLoadVisitor(ast.NodeVisitor):
    def __init__(self):
        self.pairs = {}
    
    def visit_Assign(self, node):
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Str)
        ):
            var_name = node.targets[0].id
            var_value = node.value.s
            self.pairs[var_name] = var_value
        self.generic_visit(node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute):
            if (
                node.func.value.attr == 'hub'
                and node.func.value.value.id == 'torch'
                and node.func.attr == 'load'
            ):
                args = node.args
                keywords = node.keywords
                if args:
                    repo_or_dir = self.get_arg_value(args[0])
                    model = self.get_arg_value(args[1])
                    self.pairs['repo_or_dir'] = [repo_or_dir] if self.pairs.get('repo_or_dir') is None else self.pairs['repo_or_dir'] + [repo_or_dir]
                    self.pairs['model'] = [model] if self.pairs.get('model') is None else self.pairs['model'] + [model]
                for kwarg in keywords:
                    arg_name = kwarg.arg
                    arg_value = self.get_arg_value(kwarg.value)
                    if arg_name == 'repo_or_dir' or arg_name == 'model':
                        self.pairs[arg_name] = [arg_value] if self.pairs.get(arg_name) is None else self.pairs[arg_name] + [arg_value]
                    else:
                        self.pairs[arg_name] = arg_value
        self.generic_visit(node)
    
    def get_arg_value(self, arg_node):
        if isinstance(arg_node, ast.Str):
            return arg_node.s
        elif isinstance(arg_node, ast.Name):
            return self.pairs.get(arg_node.id, '')
        return ''

def get_repo_and_model_pairs_from_snippet(snippet):
    try:
        parsed_tree : ast.Module = ast.parse(snippet, type_comments=True)
    except SyntaxError:
        return [], []
    visitor = HubLoadVisitor()
    visitor.visit(parsed_tree)
    repos = visitor.pairs.get('repo_or_dir', [])
    models = visitor.pairs.get('model', [])
    commented_calls = re.findall(r"#.*torch\.hub\.load\(([^)]+)\)", snippet)

    for call in commented_calls:
        args = call.strip().split(',')
        for i in range(len(args)):
            try:
                arg = re.search(r'[\'\"](.+?)[\'\"]', args[i].strip(), re.DOTALL).group(0)
            except AttributeError:
                print(f"Error parsing arg: {args[i]}")
                continue
            if arg.startswith("'") or arg.startswith('"'):
                arg = arg[1:]
            if arg.endswith("'") or arg.endswith('"'):
                arg = arg[:-1]
            args[i] = arg
        
        repos.append(args[0])
        models.append(args[1])

    return repos, models

def get_code_snippets(readme_content):
    return re.findall(r'```(?:python)(.*?)```', readme_content, re.DOTALL)

import torch
import torchvision

if __name__ == "__main__":
    table = etl.fromcsv("pytorch_transformed_dedup_full.csv")
    table = etl.convert(table, 'context_id', lambda v: v.rsplit('/', 1)[1])
    table.tocsv("pytorch_transformed_dedup_full_model_context_id.csv")
    # table = etl.fromcsv("pytorch_transformed_dedup.csv")
    # table = etl.addfield(table, 'repo_or_dir', lambda row: row['context_id'].rsplit('/', 1)[0])
    # table = etl.addfield(table, 'model', lambda row: row['context_id'].rsplit('/', 1)[1])
    # all_hub_models = set(etl.values(table, 'model'))
    # vision_models = set(torchvision.models.list_models())
    # class_models = set(torchvision.models.list_models(module=torchvision.models))
    # quant_models = set(torchvision.models.list_models(module=torchvision.models.quantization))
    # semant_models = set(torchvision.models.list_models(module=torchvision.models.segmentation))
    # object_models = set(torchvision.models.list_models(module=torchvision.models.detection))
    # video_models = set(torchvision.models.list_models(module=torchvision.models.video))
    # optical_flow_models = set(torchvision.models.list_models(module=torchvision.models.optical_flow))

    # vision_table = etl.fromcolumns([vision_models], header=['model'])
    # table = table.cat(vision_table)
    # table = etl.mergeduplicates(table, key='model')
    # print(table.cut('repo_or_dir', 'model').lookall())
    # # now that we have all the models, we can add the pytorch/vision repo to all models without a repo
    # table = etl.convert(table, 'repo_or_dir', lambda v: 'pytorch/vision' if v == None else v)
    # print(table.cut('repo_or_dir', 'model').lookall())

    # # Then we can add the context_id to the table for all models without a context_id
    # table = etl.convert(table, 'context_id', lambda v, row: f"{row['repo_or_dir']}/{row['model']}" if row['context_id'] == None else row['context_id'], pass_row=True)

    # replace_table = str.maketrans({'“': '', '”': '', '”': '', '"': '', '"': ''})
    # # Then we can add tags to the table for all models that fall within each category
    # table = etl.convert(table, 'tags', lambda v: [tag.translate(replace_table) for tag in ast.literal_eval(v)] if v is not None else [])
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['vision'] if row['model'] in vision_models else []), pass_row=True)
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['quantization'] if row['model'] in quant_models else []), pass_row=True)
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['segmentation'] if row['model'] in semant_models else []), pass_row=True)
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['object_detection'] if row['model'] in object_models else []), pass_row=True)
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['video'] if row['model'] in video_models else []), pass_row=True)
    # table = etl.convert(table, 'tags', lambda v, row: row['tags'] + (['optical_flow'] if row['model'] in optical_flow_models else []), pass_row=True)

    # # Then we de duplicate the tags
    # table = etl.convert(table, 'tags', lambda v: list(set(v)))

    # # Then we set the library to pytorch
    # table = etl.convert(table, 'library', lambda v: 'pytorch')

    # #Then we add the repo-url for repos without a repo-url
    # table = etl.convert(table, 'repo_url', lambda v, row: f"github.com/{row['repo_or_dir']}" if v is None else v, pass_row=True)

    # # Then we remove the model and repo_or_dir columns
    # table = etl.cutout(table, 'model', 'repo_or_dir')

    # table.tocsv("pytorch_transformed_dedup_full.csv")
    # hub_models = set(torch.hub.list('pytorch/vision'))
    # print(f"All Torch Visions Models: {vision_models}\n")
    # print(f"All Class Torch Visions Models: {class_models}\n")
    # print(f"All Vision Hub Models: {hub_models}\n")
    # print(f"All Hub Models: {all_hub_models}\n")
    # print(f"All Torch vision - class torch vision: {vision_models-class_models}\n")
    # print(f"Class models - hub models: {class_models-hub_models}\n")
    # print(f"hub models - all_hub_models: {hub_models-all_hub_models}\n")

    # alphabetize set

    # with open("pytorch_files_appended.json", "r") as f:
    #     files = json.load(f)
    # for file in files:
    #     repos = file["repos"]
    #     unique_repos = set(repos)
    #     print(f"Markdown file: {file['name']}")
    #     for repo in unique_repos:
    #         print(f"Repo: {repo}")
    #         torch.hub.list(repo)
    # with open("pytorch_files.json", "r") as f:
    #     markdown_files = json.load(f)
    # appended_markdown_files = []
    # for markdown_file in markdown_files:
    #     print("=" * 50)
    #     print(markdown_file["name"])
    #     print("-" * 50)
    #     code_snippets = get_code_snippets(markdown_file["text"])
    #     print(f"Number of code snippets: {len(code_snippets)}")
    #     i = 1
    #     md_repos = []
    #     md_models = []
    #     for snippet in code_snippets:
    #         print(f"Snippet {i}:")
    #         i += 1
    #         repo_or_dir, models = get_repo_and_model_pairs_from_snippet(snippet)
    #         total_calls = len(re.findall(r"torch\.hub\.load\(([^)]+)\)", snippet))
    #         total_models = len(models)
    #         if total_calls != total_models:
    #             print(snippet)
    #             print("•" * 50)
    #             print(f"Total calls: {total_calls}")
    #             print("repo_or_dir:", repo_or_dir)
    #             print(f"Total models: {len(models)}")
    #             print("models:", models)
    #         else:
    #             print(f"Total calls matches found models: {total_calls} == {total_models}")
    #         print("-" * 50)
    #         md_repos += repo_or_dir
    #         md_models += models
    #     print()
    #     markdown_file["repos"] = md_repos
    #     markdown_file["models"] = md_models
    #     appended_markdown_files.append(markdown_file)

    # with open("pytorch_files_appended.json", "w") as f:
    #     json.dump(appended_markdown_files, f, indent=4)