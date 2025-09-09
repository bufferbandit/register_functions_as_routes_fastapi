
from types import SimpleNamespace
from fastapi import APIRouter
import inspect
import re


"""
Utility helpers for automatically registering FastAPI routes.

This module inspects functions in a given module and attaches them to any
APIRouter instances it finds. It works by:

- Extracting decorators applied to functions to check for existing routes.
- Finding APIRouter instances defined in the module.
- Auto-generating route paths from function names (underscores → dashes).
- Registering all coroutine functions as routes unless they already have a
  FastAPI decorator or are explicitly excluded with a `noroute_` prefix.

Intended for quickly exposing module functions as FastAPI endpoints with minimal
boilerplate.
"""


def get_decorator_lines(fn):
	"""Return all decorator lines above the function definition."""
	source = inspect.getsource(fn)
	func_index = source.find("def ")
	lines = source[:func_index].strip().splitlines()
	return [line.strip() for line in lines if line.strip().startswith("@")]

def parse_decorator_line(line):
	"""
	Parse a decorator line into (name, [args]).
	Example: '@router.get("/fake2")' -> ('router.get', ['/fake2'])
	"""
	deco = line.lstrip("@")
	match = re.match(r"(\w[\w\.]*)\s*(\((.*)\))?", deco)
	if not match:
		return (deco, [])
	name, _, args = match.groups()
	args_list = [arg.strip() for arg in args.split(",")] if args else []
	return SimpleNamespace(name=name, args=args_list)

def get_decorators(fn):
	"""Return a list of (decorator_name, args_list) for a function."""
	lines = get_decorator_lines(fn)
	return [parse_decorator_line(line) for line in lines]


def find_routers_in_module(module):
	"""
	Returns a dict of {variable_name: APIRouter_instance}
	for all APIRouter instances in the given module object.
	"""
	routers = {}
	for name, obj in vars(module).items():
		if isinstance(obj, APIRouter):
			routers[name] = obj
	return routers



def auto_route(router, handler, methods=None, *args, **kwargs):
	if methods is None:
		methods = ["get"]
	path = "/" + handler.__name__.replace("_", "-")
	router.add_api_route(path, handler,
						 methods=[method.upper() for method in methods], *args, **kwargs)


def register_functions_as_routes(module, methods=["get"], *args, **kwargs):
	router_name, router = next(iter(find_routers_in_module(module).items()))
	for name, fn in inspect.getmembers(module, inspect.iscoroutinefunction):
		has_fastapi_decorator = any(d.name.startswith(router_name) for d in get_decorators(fn))
		if (
				fn.__module__ == module.__name__ and
				not has_fastapi_decorator and
				not name.startswith("noroute_")
		):
			auto_route(router, fn, methods, *args, **kwargs)
