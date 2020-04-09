from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

import lxml.etree

# from future import standard_library
from lark import Lark

from ..transformer.transformer import LatexTransformer, MathMLTransformer
from ..utils.utils import check_connection, httplib

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

# standard_library.install_aliases()


class ASCIIMathTranslator(object):
    def __init__(self, grammar, *args, **kwargs):
        if "transformer" in kwargs:
            transformer = kwargs["transformer"]
            del kwargs["transformer"]
        else:
            transformer = LatexTransformer(log=True)
        if "lexer" in kwargs:
            lexer = kwargs["lexer"]
            del kwargs["lexer"]
        else:
            lexer = "contextual"
        if "parser" in kwargs:
            parser = kwargs["parser"]
            del kwargs["parser"]
        else:
            parser = "lalr"
        if "inplace" in kwargs:
            inplace = kwargs["inplace"]
            del kwargs["inplace"]
        else:
            inplace = False
        self.inplace = inplace
        self.grammar = grammar
        self.transformer = transformer
        if inplace:
            kwargs.update({"transformer": transformer})
        self.parser = Lark(
            grammar, *args, parser=parser, lexer=lexer, **kwargs
        )

    def translate(self, s, pprint=False):
        if not self.inplace:
            parsed = self.parser.parse(s)
            if pprint:
                print(parsed.pretty())
            return self.transformer.transform(parsed)
        else:
            return self.parser.parse(s)


class ASCIIMath2Tex(ASCIIMathTranslator):
    def __init__(self, grammar, *args, **kwargs):
        if "log" in kwargs:
            log = kwargs["log"]
            del kwargs["log"]
        else:
            log = False
        super(ASCIIMath2Tex, self).__init__(
            grammar, *args, transformer=LatexTransformer(log=log), **kwargs
        )

    def translate(self, s, pprint=False):
        """
            \\documentclass{article}
            \\usepackage[active]{preview}
            \\begin{document}
            \\begin{preview}
            \\[
            \\pi = \\sqrt{12}\\sum^\\infty_{k=0} \\frac{ (-3)^{-k} }{ 2k+1 }
            \\]
            \\end{preview}
            \\end{document}
        """
        return super(ASCIIMath2Tex, self).translate(s, pprint=pprint)


class ASCIIMath2MathML(ASCIIMathTranslator):
    def __init__(self, grammar, *args, **kwargs):
        if "log" in kwargs:
            log = kwargs["log"]
            del kwargs["log"]
        else:
            log = False
        super(ASCIIMath2MathML, self).__init__(
            grammar, *args, transformer=MathMLTransformer(log=log), **kwargs
        )

    def __dtd_validation(self, xml, dtd_validation):
        if check_connection():
            logging.info("LOADING DTD...")
            lxml_parser = lxml.etree.XMLParser(
                dtd_validation=dtd_validation,
                no_network=False,
                load_dtd=True,
                ns_clean=True,
            )
            logging.info(
                "PARSING{}XML...".format(
                    " AND VALIDATING " if dtd_validation else " "
                )
            )
            try:
                return True, lxml.etree.fromstring(xml, lxml_parser)
            except lxml.etree.XMLSyntaxError as XMLSE:
                return False, str(XMLSE)
        else:
            return False, "No connection available to check against DTD"

    def translate(
        self,
        s,
        displaystyle=False,
        dtd=None,
        xml=False,
        dtd_validation=False,
        pprint=False,
    ):
        if displaystyle:
            dstyle = '<mstyle displaystyle="true">{}</mstyle>'
        else:
            dstyle = "{}"
        if dtd is None or dtd.lower() == "mathml3":
            dtd_head = (
                '<!DOCTYPE math PUBLIC "-//W3C//DTD MathML 3.0//EN" '
                + '"http://www.w3.org/Math/DTD/mathml3/mathml3.dtd">'
            )
        elif dtd.lower() == "mathml1":
            dtd_head = (
                "<!DOCTYPE math SYSTEM "
                + '"http://www.w3.org/Math/DTD/mathml1/mathml.dtd">'
            )
        elif dtd.lower() == "mathml2":
            dtd_head = (
                '<!DOCTYPE math PUBLIC "-//W3C//DTD MathML 2.0//EN" '
                + '"http://www.w3.org/Math/DTD/mathml2/mathml2.dtd">'
            )
        else:
            raise NotImplementedError("DTD validation only against MathML DTD 1, 2 or 3")
        parsed = (
            dtd_head
            + "<math"
            + (
                " xmlns='http://www.w3.org/1998/Math/MathML'"
                if dtd != "mathml1"
                else ""
            )
            + ">"
            + dstyle.format(super(ASCIIMath2MathML, self).translate(s, pprint))
            + "</math>"
        )
        if xml:
            ok, root = self.__dtd_validation(parsed, dtd_validation)
            return (
                ok,
                lxml.etree.tostring(root).decode("utf-8") if ok else root,
            )
        else:
            return True, parsed
