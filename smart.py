import ast
import time
import os


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
        # print(node, dir(node))
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
        # print(node_name)
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
        # print(ast_list)
        # time.sleep(1)
        result = []

        heads = get_heads(ast_list)

        tails = get_tails(ast_list)

        # if all([isinstance(h, tuple) for h in heads]): result += '('

        if all([h == [] for h in heads]): return ''
        if any([h == [] for h in heads]): return '*'

        if all([comparable(el) for el in heads]):
            if len(set(heads)) == 1:  # compare
                result.append(heads[0])  # return common item
            else:
                result.append('?')  # differ
        else:
            result += [self.get_common_expr(heads)]
        # print(result)
        result += self.get_common_expr(tails)
        return result


class ASTGenerator(object):
    def __init__(self, code):
        self.code = code
        self.ast = ast.parse(code)
        # print(ast.dump(self.ast))
        self.parsed_ast = ASTTranslator().walk(self.ast)[1]
        # print(self.parsed_ast)


class CodeSearcher(object):
    def __init__(self, db):
        self.db = db

    def match_expr(self, query):
        expr, pattern = query
        # print(expr, pattern)
        # print(time.sleep(1))

        heads = get_heads([expr, pattern])
        # print('Heads: ', heads)
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

    def search(self, tag):
        result = []
        for ex, tags in self.db:
            if any([tag in t for t in tags]):
                result.append(ex)
        return result


if __name__ == "__main__":
    BASE_DIR = 'codes/learn/'
    exprs = []
    codes = []
    for f in os.listdir(BASE_DIR):
        code = open(os.path.join(BASE_DIR, f)).read()
        # print(code)
        ast_expr = ASTGenerator(code).parsed_ast[0]
        # print(ast_expr)
        # print('*'*80)
        exprs.append(ast_expr)
        codes.append(code)

    search_code = open(os.path.join('codes/search', 'source1.py')).read()

    ast_pm = ASTPatternMatcher()
    common_expr = ast_pm.get_common_expr(exprs)
    print(common_expr)

    # TODO: extract via re cprop, cprops, tags and search among them
    # TODO: add CodeItem class
    # TODO: add separate DB for expr <-> tag
    tags = [
        'class with prop v1',
        'cprop v1',  # class prop
        '#base cprop v1'
    ]

    code_db = [(common_expr, codes)]
    expr_db = [(common_expr, tags)]
    s = CodeSearcher(code_db)

    expr = ASTGenerator(search_code).parsed_ast[0]
    for code in s.search(expr):
        print('By code', code)

    es = ExprSearcher(expr_db)
    for expr in es.search(tags[0]):
        for code in s.search(expr):
            print('By tag', code)
