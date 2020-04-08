from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

# from future import standard_library
from lark import Lark

from ..transformer.transformer import LatexTransformer, MathMLTransformer

# standard_library.install_aliases()


class ASCIIMathTranslator(object):
    def __init__(self, grammar, *args, **kwargs):
        if "transformer" in kwargs:
            transformer = kwargs["transformer"]
            del kwargs["transformer"]
        else:
            transformer = LatexTransformer()
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
        super(ASCIIMath2Tex, self).__init__(
            grammar, *args, transformer=LatexTransformer(), **kwargs
        )


class ASCIIMath2MathML(ASCIIMathTranslator):
    def __init__(self, grammar, *args, **kwargs):
        super(ASCIIMath2MathML, self).__init__(
            grammar, *args, transformer=MathMLTransformer(), **kwargs
        )
