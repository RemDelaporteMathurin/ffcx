
import inspect
import re
from string import Formatter

from ufl import product
from ffc.log import error, warning
from ffc.backends.ufc import *

from uflacs.language.format_lines import format_indented_lines
from uflacs.backends.ufc.templates import *

#__all__ = (["ufc_form", "ufc_dofmap", "ufc_finite_element", "ufc_integral"]
#           + ["ufc_%s_integral" % integral_type for integral_type in integral_types])


# These are all the integral types directly supported in ufc.
# TODO: Get these from somewhere for more automation.
ufc_integral_types = ("cell", "exterior_facet", "interior_facet", "vertex", "custom")


# These are the method names in ufc::form that are specialized for each integral type
integral_name_templates = (
    "max_%s_subdomain_id",
    "has_%s_integrals",
    "create_%s_integral",
    "create_default_%s_integral",
    )


class ufc_generator(object):
    """Common functionality for code generators producing ufc classes.

    The generate function is the driver for generating code for a class.
    It automatically extracts template keywords and inserts the results
    from calls to self.<keyword>(language, ir), or the value of ir[keyword]
    if there is no self.<keyword>.
    """
    def __init__(self, header_template, implementation_template):
        self._header_template = header_template
        self._implementation_template = implementation_template

        r = re.compile(r"%\(([a-zA-Z0-9_]*)\)")
        self._header_keywords = set(r.findall(self._header_template))
        self._implementation_keywords = set(r.findall(self._implementation_template))

        self._keywords = sorted(self._header_keywords | self._implementation_keywords)

    def generate_snippets(self, L, ir):
        # Generate code snippets for each keyword found in templates
        snippets = {}
        for kw in self._keywords:
            # Check that attribute self.<keyword> is available
            if not hasattr(self, kw):
                error("Missing handler for keyword '%s' in class %s." % (kw, self.__class__.__name__))

            # Could check for existence of keyword in ir too but I'd
            # rather redesign so ir contains better defined entries:
            #if kw not in ir:
            #    error("Missing entry for keyword '%s' in ir for class %s." % (kw, self.__class__.__name__))

            # Call self.<keyword>(L, ir) to get value
            method = getattr(self, kw)
            value = method(L, ir)
            if isinstance(value, L.CStatement):
                value = L.Indented(value.cs_format())
                value = format_indented_lines(value)
            snippets[kw] = value

        # Error checking (can detect some bugs early when changing the interface)
        valueonly = {"classname"}
        attrs = set(name for name in dir(self) if not name.startswith("_"))
        base_attrs = set(name for name in dir(ufc_generator) if not name.startswith("_"))
        base_attrs.add("generate_snippets")
        base_attrs.add("generate")
        unused = attrs - set(self._keywords) - base_attrs
        missing = set(self._keywords) - attrs - valueonly
        if unused:
            warning("*** Unused generator functions:\n%s" % ('\n'.join(map(str,sorted(unused))),))
        if missing:
            warning("*** Missing generator functions:\n%s" % ('\n'.join(map(str,sorted(missing))),))

        return snippets

    def generate(self, L, ir, snippets=None):
        "Return composition of templates with generated snippets."
        if snippets is None:
            snippets = self.generate_snippets(L, ir)
        h = self._header_template % snippets
        cpp = self._implementation_template % snippets
        return h, cpp

    def classname(self, L, ir):
        "Return classname."
        classname = ir["classname"]
        return classname

    def members(self, L, ir):
        "Return empty string. Override in classes that need members."
        assert not ir.get("members")
        return ""

    def constructor(self, L, ir):
        "Return empty string. Override in classes that need constructor."
        assert not ir.get("constructor")
        return ""

    def constructor_arguments(self, L, ir):
        "Return empty string. Override in classes that need constructor."
        assert not ir.get("constructor_arguments")
        return ""

    def initializer_list(self, L, ir):
        "Return empty string. Override in classes that need constructor."
        assert not ir.get("initializer_list")
        return ""

    def destructor(self, L, ir):
        "Return empty string. Override in classes that need destructor."
        assert not ir.get("destructor")
        return ""

    def signature(self, L, ir):
        "Default implementation of returning signature string fetched from ir."
        sig = ir["signature"]
        return L.Return(L.LiteralString(sig))

    def create(self, L, ir):
        "Default implementation of creating a new object of the same type."
        classname = ir["classname"]
        return L.Return(L.New(classname))

    def topological_dimension(self, L, ir):
        "Default implementation of returning topological dimension fetched from ir."
        tdim = ir["topological_dimension"]
        return L.Return(L.LiteralInt(tdim))

    def geometric_dimension(self, L, ir):
        "Default implementation of returning geometric dimension fetched from ir."
        gdim = ir["geometric_dimension"]
        return L.Return(L.LiteralInt(gdim))
