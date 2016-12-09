# -*- coding: utf-8 -*-
"""
    sphinx.util.docutils
    ~~~~~~~~~~~~~~~~~~~~

    Utility functions for docutils.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

from copy import copy
from contextlib import contextmanager

from docutils.parsers.rst import directives, roles

if False:
    # For type annotation
    from typing import Any, Callable, Iterator, Tuple  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


@contextmanager
def docutils_namespace():
    # type: () -> Iterator[None]
    """Create namespace for reST parsers."""
    try:
        _directives = copy(directives._directives)
        _roles = copy(roles._roles)

        yield
    finally:
        directives._directives = _directives
        roles._roles = _roles


class ElementLookupError(Exception):
    pass


class sphinx_domains(object):
    """Monkey-patch directive and role dispatch, so that domain-specific
    markup takes precedence.
    """
    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env
        self.directive_func = None  # type: Callable
        self.roles_func = None  # type: Callable

    def __enter__(self):
        self.enable()

    def __exit__(self, type, value, traceback):
        self.disable()

    def enable(self):
        self.directive_func = directives.directive
        self.role_func = roles.role

        directives.directive = self.lookup_directive
        roles.role = self.lookup_role

    def disable(self):
        directives.directive = self.directive_func
        roles.role = self.role_func

    def lookup_domain_element(self, type, name):
        # type: (unicode, unicode) -> Tuple[Any, List]
        """Lookup a markup element (directive or role), given its name which can
        be a full name (with domain).
        """
        name = name.lower()
        # explicit domain given?
        if ':' in name:
            domain_name, name = name.split(':', 1)
            if domain_name in self.env.domains:
                domain = self.env.get_domain(domain_name)
                element = getattr(domain, type)(name)
                if element is not None:
                    return element, []
        # else look in the default domain
        else:
            def_domain = self.env.temp_data.get('default_domain')
            if def_domain is not None:
                element = getattr(def_domain, type)(name)
                if element is not None:
                    return element, []

        # always look in the std domain
        element = getattr(self.env.get_domain('std'), type)(name)
        if element is not None:
            return element, []

        raise ElementLookupError

    def lookup_directive(self, name, lang_module, document):
        # type: (unicode, unicode, nodes.document) -> Tuple[Any, List]
        try:
            return self.lookup_domain_element('directive', name)
        except ElementLookupError:
            return self.directive_func(name, lang_module, document)

    def lookup_role(self, name, lang_module, lineno, reporter):
        # type: (unicode, unicode, int, Any) -> Tuple[Any, List]
        try:
            return self.lookup_domain_element('role', name)
        except ElementLookupError:
            return self.role_func(name, lang_module, lineno, reporter)
