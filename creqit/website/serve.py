from werkzeug.wrappers import Response

import creqit
from creqit.website.page_renderers.error_page import ErrorPage
from creqit.website.page_renderers.not_found_page import NotFoundPage
from creqit.website.page_renderers.not_permitted_page import NotPermittedPage
from creqit.website.page_renderers.redirect_page import RedirectPage
from creqit.website.path_resolver import PathResolver


def get_response(path=None, http_status_code=200) -> Response:
	"""Resolves path and renders page"""
	response = None
	path = path or creqit.local.request.path
	endpoint = path

	try:
		path_resolver = PathResolver(path, http_status_code)
		endpoint, renderer_instance = path_resolver.resolve()
		response = renderer_instance.render()
	except creqit.Redirect as e:
		return RedirectPage(endpoint or path, e.http_status_code).render()
	except creqit.PermissionError as e:
		response = NotPermittedPage(endpoint, http_status_code, exception=e).render()
	except creqit.PageDoesNotExistError:
		response = NotFoundPage(endpoint, http_status_code).render()
	except Exception as e:
		response = ErrorPage(exception=e).render()

	return response


def get_response_content(path=None, http_status_code=200) -> str:
	response = get_response(path, http_status_code)
	return str(response.data, "utf-8")


def get_response_without_exception_handling(path=None, http_status_code=200) -> Response:
	"""Resolves path and renders page.

	Note: This doesn't do any exception handling and assumes you'll implement the exception
	handling that's required."""
	path = path or creqit.local.request.path

	path_resolver = PathResolver(path, http_status_code)
	_endpoint, renderer_instance = path_resolver.resolve()
	return renderer_instance.render()
