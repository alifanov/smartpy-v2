import ast
import time
import os
import re
from exprs import exprs as exprs_db


def get_heads(l):
    heads = []
    for s in l:
        if s:
            heads.append(s[0])
        else:
            heads.append([])
    return heads


def get_tails(l):
    tails = []
    for s in l:
        if s:
            tails.append(s[1:])
        else:
            tails.append([])
    return tails


class ASTTranslator(object):
    node_map = {
        'ClassDef': 'class',
        'Module': 'module',
        'Assign': '=',
        'Name': 'var',
        'Num': 'num',
    }

    def walk(self, node):
        result = []
        node_name = node.__class__.__name__
        if node_name in self.node_map:
            node_name = self.node_map[node_name]
        if node_name == 'module':
            result += [node_name, list([self.walk(s) for s in node.body])]
        elif node_name == 'class':
            result += [node_name, node.name, list([self.walk(s) for s in node.body])]
        elif node_name == '=':
            result += [node_name, self.walk(node.targets), self.walk(node.value)]
        elif node_name == 'var':
            result = node.id
        elif node_name == 'num':
            result = node.n
        elif node_name == 'list':
            if len(node) == 1:
                result = self.walk(node[0])
            else:
                result = list([self.walk(s) for s in node])
        else:
            result += [node_name, ]
        return result


def comparable(v):
    for cls in [
        str,
        int
    ]:
        if isinstance(v, cls): return True
    return False


class ASTPatternMatcher(object):
    def get_common_expr(self, ast_list):
        result = []

        heads = get_heads(ast_list)

        tails = get_tails(ast_list)

        if all([h == [] for h in heads]): return ''
        if any([h == [] for h in heads]): return '*'

        if all([comparable(el) for el in heads]):
            if len(set(heads)) == 1:  # compare
                result.append(heads[0])  # return common item
            else:
                result.append('?')  # differ
        else:
            result += [self.get_common_expr(heads)]
        result += self.get_common_expr(tails)
        return result


class ASTGenerator(object):
    def __init__(self, code):
        self.code = code
        self.ast = ast.parse(code)
        self.parsed_ast = ASTTranslator().walk(self.ast)[1]


class CodeSearcher(object):
    def __init__(self, db):
        self.db = db

    def match_expr(self, query):
        expr, pattern = query

        heads = get_heads([expr, pattern])
        tails = get_tails([expr, pattern])

        if all([h == [] for h in heads]): return True

        if heads[1] == '*': return True

        if all([comparable(el) for el in heads]):
            if heads[1] == '*':
                return True
            if heads[1] == '?':
                if not heads[0]:
                    return False
                return True
            if heads[1] != heads[0]:
                return False
        else:
            if not self.match_expr(heads):
                return False
        return self.match_expr(tails)

    def search(self, expr):
        for k, v in self.db:
            if self.match_expr([expr, k]):
                return v
        return []


class ExprSearcher(object):
    def __init__(self, db):
        self.db = db

    def extract_tags(self, s):
        m = re.findall(r'#([a-zA-Z^:space:]+)', s)
        return m

    def extract_cprops(self, s):
        m = re.findall(r'cprop ([a-z0-9]+)', s)
        return m

    def search(self, q, fuzzy=False):
        result = []
        tags = self.extract_tags(q)
        cprops = self.extract_cprops(q)
        for s, ex in self.db:
            if tags:
                db_tags = self.extract_tags(s)
                if set(db_tags)&set(tags):
                    result.append(ex)
                continue

            db_cprops = self.extract_cprops(s)
            if set(db_cprops)&set(cprops) or fuzzy:
                result.append(ex)
                continue
        return result


if __name__ == "__main__":
    BASE_DIR = 'codes/learn/'
    exprs = []
    codes = []
    for f in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, f)
        if os.path.isfile(path):
            code = open(path).read()
            ast_expr = ASTGenerator(code).parsed_ast[0]
            exprs.append(ast_expr)
            codes.append(code)

    search_code = open(os.path.join('codes/search', 'source1.py')).read()

    ast_pm = ASTPatternMatcher()
    common_expr = ast_pm.get_common_expr(exprs)

    # TODO: add CodeItem class

    code_db = [(common_expr, codes)]
    s = CodeSearcher(code_db)

    expr = ASTGenerator(search_code).parsed_ast[0]
    for code in s.search(expr):
        print('By code', code)

    es = ExprSearcher(exprs_db)
    for expr in es.search('#base cprop v1', fuzzy=True):
        print('By expr: ', expr)
