--context_id,model_hub,sha,repo_url,original_data,downloads,likes

--write a query to join the model table with all the other tables that are linked through a junction table

CREATE TABLE model (
	id integer PRIMARY KEY AUTOINCREMENT,
	context_id text,
	model_hub text,
	sha text,
	repo_url text,
	excess_metadata blob,
	downloads integer,
	likes integer
);

CREATE TABLE model_hub (
	model_hub_id integer PRIMARY KEY AUTOINCREMENT,
	url text,
	name text
);

CREATE TABLE tag (
	tag_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE framework (
	framework_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE architecture (
	architecture_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE dataset (
	id integer PRIMARY KEY AUTOINCREMENT,
	model_hub integer,
	context_id integer,
	description text
);

CREATE TABLE language (
	language_id integer PRIMARY KEY AUTOINCREMENT,
	abbreviation text
);

CREATE TABLE author (
	author_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE library (
	library_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE paper (
	paper_id integer PRIMARY KEY AUTOINCREMENT,
	url text
);

CREATE TABLE license (
	license_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE dataset_info (
	info_id integer PRIMARY KEY AUTOINCREMENT,
	file jsonb
);

CREATE TABLE representation (
	representation_id integer PRIMARY KEY AUTOINCREMENT,
	name text
);

CREATE TABLE usage (
	usage_id integer PRIMARY KEY AUTOINCREMENT,
	occcurences integer,
	model_id integer
);

CREATE TABLE reuse_repository (
	id integer PRIMARY KEY AUTOINCREMENT,
	github_url text,
	files text,
	commit_history text
);

CREATE TABLE issues (
	id integer PRIMARY KEY AUTOINCREMENT,
	issue blob
);

CREATE TABLE pull_requests (
	pr_id integer PRIMARY KEY AUTOINCREMENT,
	pull_request blob
);

CREATE TABLE model_to_reuse (
	model_id integer,
	reuse_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (reuse_id) REFERENCES reuse_repository(id)
);

CREATE TABLE reuse_to_issues (
	reuse_id integer,
	issue_id integer,
	FOREIGN KEY (reuse_id) REFERENCES reuse_repository(id),
	FOREIGN KEY (issue_id) REFERENCES issues(id)
);

CREATE TABLE reuse_to_prs (
	reuse_id integer,
	pr_id integer,
	FOREIGN KEY (reuse_id) REFERENCES reuse_repository(id),
	FOREIGN KEY (pr_id) REFERENCES pull_requests(id)
);

CREATE TABLE model_to_tag (
	model_id integer,
	tag_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (tag_id) REFERENCES tag(tag_id)
);

CREATE TABLE model_hub_to_tag (
	model_hub_id integer,
	tag_id integer,
	FOREIGN KEY (model_hub_id) REFERENCES model_hub(model_hub_id),
	FOREIGN KEY (tag_id) REFERENCES tag(tag_id)
);

CREATE TABLE dataset_to_tag (
	dataset_id integer,
	tag_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (tag_id) REFERENCES tag(tag_id)
);

CREATE TABLE model_to_language (
	model_id integer,
	language_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (language_id) REFERENCES language(language_id)
);

CREATE TABLE dataset_to_language (
	dataset_id integer,
	language_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (language_id) REFERENCES language(language_id)
);

CREATE TABLE model_to_framework (
	model_id integer,
	framework_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (framework_id) REFERENCES framework(framework_id)
);

CREATE TABLE model_to_architecture (
	model_id integer,
	architecture_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (architecture_id) REFERENCES architecture(architecture_id)
);

CREATE TABLE model_to_author (
	model_id integer,
	author_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (author_id) REFERENCES author(author_id)
);

CREATE TABLE model_to_library (
	model_id integer,
	library_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (library_id) REFERENCES library(library_id)
);

CREATE TABLE model_to_paper (
	model_id integer,
	paper_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

CREATE TABLE dataset_to_paper (
	dataset_id integer,
	paper_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (paper_id) REFERENCES paper(paper_id)
);

CREATE TABLE model_to_dataset (
	dataset_id integer,
	model_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (model_id) REFERENCES model(id)
);

CREATE TABLE model_to_license (
	model_id integer,
	license_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (license_id) REFERENCES license(license_id)
);

CREATE TABLE dataset_to_license (
	dataset_id integer,
	license_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (license_id) REFERENCES license(license_id)
);

CREATE TABLE dataset_to_info (
	dataset_id integer,
	info_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (info_id) REFERENCES dataset_info(info_id)
);

CREATE TABLE dataset_to_author (
	dataset_id integer,
	author_id integer,
	FOREIGN KEY (dataset_id) REFERENCES dataset(id),
	FOREIGN KEY (author_id) REFERENCES author(author_id)
);

CREATE TABLE model_to_representation (
	model_id integer,
	representation_id integer,
	FOREIGN KEY (model_id) REFERENCES model(id),
	FOREIGN KEY (representation_id) REFERENCES representation(representation_id)
);






































