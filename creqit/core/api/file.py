import json

import creqit
from creqit.core.doctype.file.file import File
from creqit.core.doctype.file.utils import setup_folder_path
from creqit.utils import cint, cstr


@creqit.whitelist()
def unzip_file(name: str):
	"""Unzip the given file and make file records for each of the extracted files"""
	file: File = creqit.get_doc("File", name)
	return file.unzip()


@creqit.whitelist()
def get_attached_images(doctype: str, names: list[str] | str) -> creqit._dict:
	"""Return list of image urls attached in form `{name: ['image.jpg', 'image.png']}`."""

	if isinstance(names, str):
		names = json.loads(names)

	img_urls = creqit.db.get_list(
		"File",
		filters={
			"attached_to_doctype": doctype,
			"attached_to_name": ("in", names),
			"is_folder": 0,
		},
		fields=["file_url", "attached_to_name as docname"],
	)

	out = creqit._dict()
	for i in img_urls:
		out[i.docname] = out.get(i.docname, [])
		out[i.docname].append(i.file_url)

	return out


@creqit.whitelist()
def get_files_in_folder(folder: str, start: int = 0, page_length: int = 20) -> dict:
	attachment_folder = creqit.db.get_value(
		"File",
		"Home/Attachments",
		["name", "file_name", "file_url", "is_folder", "modified"],
		as_dict=1,
	)

	files = creqit.get_list(
		"File",
		{"folder": folder},
		["name", "file_name", "file_url", "is_folder", "modified"],
		start=start,
		page_length=page_length + 1,
	)

	if folder == "Home" and attachment_folder not in files:
		files.insert(0, attachment_folder)

	return {"files": files[:page_length], "has_more": len(files) > page_length}


@creqit.whitelist()
def get_files_by_search_text(text: str) -> list[dict]:
	if not text:
		return []

	text = "%" + cstr(text).lower() + "%"
	return creqit.get_list(
		"File",
		fields=["name", "file_name", "file_url", "is_folder", "modified"],
		filters={"is_folder": False},
		or_filters={
			"file_name": ("like", text),
			"file_url": text,
			"name": ("like", text),
		},
		order_by="creation desc",
		limit=20,
	)


@creqit.whitelist(allow_guest=True)
def get_max_file_size() -> int:
	return (
		cint(creqit.get_system_settings("max_file_size")) * 1024 * 1024
		or cint(creqit.conf.get("max_file_size"))
		or 25 * 1024 * 1024
	)


@creqit.whitelist()
def create_new_folder(file_name: str, folder: str) -> File:
	"""create new folder under current parent folder"""
	file = creqit.new_doc("File")
	file.file_name = file_name
	file.is_folder = 1
	file.folder = folder
	file.insert(ignore_if_duplicate=True)
	return file


@creqit.whitelist()
def move_file(file_list: list[File | dict] | str, new_parent: str, old_parent: str) -> None:
	if isinstance(file_list, str):
		file_list = json.loads(file_list)

	# will check for permission on each file & update parent
	for file_obj in file_list:
		setup_folder_path(file_obj.get("name"), new_parent)

	# recalculate sizes
	creqit.get_doc("File", old_parent).save()
	creqit.get_doc("File", new_parent).save()


@creqit.whitelist()
def zip_files(files: str):
	files = creqit.parse_json(files)
	creqit.response["filename"] = "files.zip"
	creqit.response["filecontent"] = File.zip_files(files)
	creqit.response["type"] = "download"
