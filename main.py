# Mini-Lisp Interpreter

from ply.lex import lex
from ply.yacc import yacc
from collections import deque, defaultdict

import networkx as nx
import matplotlib.pyplot as plt
from copy import deepcopy

IS_DEBUG = False


# --- Lexer ---
class Node:
    node_counter = 0

    def __init__(self, node_type, children=None, value=None):
        self.type = node_type
        self.value = value
        self.parent = None
        self.id = Node.node_counter
        Node.node_counter += 1
        if children:
            self.children = children
        else:
            self.children = []

    def __repr__(self):
        return f'Node({self.type!r}, {self.value!r},{self.children!r})'


reserved = {
    'print-num': 'PRINT_NUM',
    'print-bool': 'PRINT_BOOL',
    'mod': 'MOD',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'define': 'DEF',
    'if': 'IF',
    'fun': 'FUN',
}

tokens = [
             "NUMBER", "BOOL", "PLUS", "MINUS", "MUL", "DIV", "Greater", "Less", "Equal", "ID", "LPAREN",
             "RPAREN"] + list(reserved.values())

literals = ['(', ')', '+', '-', '*', '/', '>', '<', '=']

# Tokens
t_PRINT_NUM = r'print-num'
t_PRINT_BOOL = r'print-bool'
t_MOD = r'mod'
t_AND = r'and'
t_OR = r'or'
t_NOT = r'not'
t_DEF = r'define'
t_IF = r'if'
t_FUN = r'fun'
t_PLUS = r'\+'
t_MINUS = r'\-'
t_MUL = r'\*'
t_DIV = r'/'
t_Greater = r'>'
t_Less = r'<'
t_Equal = r'='
t_LPAREN = r'\('
t_RPAREN = r'\)'
# \t|\n|\r => ignore white spaces
t_ignore = ' \t\n\r'


def t_NUMBER(t):
    r'0|[1-9][0-9]*|\-[1-9][0-9]*'
    t.value = Node('NUMBER', value=int(t.value))
    return t


def t_BOOL(t):
    r'\#t|\#f'
    if t.value == '#t':
        t.value = Node('BOOL', value=True)
    else:
        t.value = Node('BOOL', value=False)
    return t


def t_ID(t):
    r'[a-z]([a-z]|[0-9]|\-)*'
    # 特別小心對關鍵字的影響
    t.type = reserved.get(t.value, 'ID')  # Check for reserved words
    if t.type == 'ID':
        t.value = Node('ID', value=t.value)
    return t


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex()
input_file = open("input.txt", "r")
data = input_file.read()
lexer.input(data)

# Tokenize
if IS_DEBUG:
    print("Tokens:")
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok.type, tok.value)

    print('---' * 10)

# --- Parser ---
# Parsing rules

IS_VALID_SYNTAX = True


def p_PROGRAM(p):
    """
    PROGRAM : STMTS
    """
    p[0] = p[1]
    if IS_VALID_SYNTAX and IS_DEBUG:
        print("Accepted")


def p_STMTS(p):
    """
    STMTS : STMT
          | STMT STMTS
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('STMTS', [p[1], p[2]])


def p_STMT(p):
    """
    STMT : EXP
        | PRINT_STMT
        | DEF_STMT
    """
    p[0] = p[1]


def p_PRINT_STMT(p):
    """
    PRINT_STMT : LPAREN PRINT_NUM  EXP RPAREN
               | LPAREN PRINT_BOOL  EXP RPAREN
    """
    if p[2] == 'print-num':
        p[0] = Node('PRINT_NUM', [p[3]])
    else:
        p[0] = Node('PRINT_BOOL', [p[3]])


def p_EXP(p):
    """
    EXP : NUMBER
        | BOOL
        | VARIABLE
        | NUM_OP
        | LOGICAL_OP
        | FUN_EXP
        | FUN_CALL
        | IF_EXP
    """
    p[0] = p[1]


def p_EXPS(p):
    """
    EXPS : EXP
         | EXP EXPS
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Node('EXPS', [p[1], p[2]])


def p_NUM_OP(p):
    """
    NUM_OP : LPAREN PLUS EXP EXPS RPAREN
           | LPAREN MINUS EXP EXP RPAREN
           | LPAREN MUL EXP EXPS RPAREN
           | LPAREN DIV EXP EXP RPAREN
           | LPAREN MOD EXP EXP RPAREN
           | LPAREN Greater EXP EXP RPAREN
           | LPAREN Less EXP EXP RPAREN
           | LPAREN Equal EXP EXPS RPAREN
    """
    match p[2]:
        case '+':
            p[0] = Node('PLUS', [p[3], p[4]])
            # print(p[0].children)
        case '-':
            p[0] = Node('MINUS', [p[3], p[4]])
        case '*':
            p[0] = Node('MUL', [p[3], p[4]])
        case '/':
            p[0] = Node('DIV', [p[3], p[4]])
        case '>':
            p[0] = Node('GREATER', [p[3], p[4]])
        case '<':
            p[0] = Node('LESS', [p[3], p[4]])
        case '=':
            p[0] = Node('EQUAL', [p[3], p[4]])
        case 'mod':
            p[0] = Node('MOD', [p[3], p[4]])


def p_LOGICAL_OP(p):
    """
    LOGICAL_OP : LPAREN AND EXP EXPS RPAREN
               | LPAREN OR EXP EXPS RPAREN
               | LPAREN NOT EXP RPAREN
    """
    match p[2]:
        case 'and':
            p[0] = Node('AND', [p[3], p[4]])
        case 'or':
            p[0] = Node('OR', [p[3], p[4]])
        case 'not':
            p[0] = Node('NOT', [p[3]])


def p_DEF_STMT(p):
    """
    DEF_STMT : LPAREN DEF VARIABLE EXP RPAREN
             | LPAREN DEF FUN_NAME FUN_EXP RPAREN
    """
    # 語法可能還要再修改，TEMP FIXED
    if p[4].type == 'FUN_EXP':
        p[3].type = 'FUN_NAME'
    p[0] = Node('DEF', [p[3], p[4]])


def p_VARIABLE(p):
    """
    VARIABLE : ID
    """
    p[0] = Node('VARIABLE', [p[1]])


def p_VARIABLES(p):
    """
    VARIABLES : VARIABLE VARIABLES
              | empty
    """
    if len(p) == 3:
        p[0] = Node('VARIABLES', [p[1], p[2]])
    else:
        p[0] = Node('NULL')


def p_FUN_EXP(p):
    """
    FUN_EXP : LPAREN FUN FUN_IDs FUN_BODY RPAREN
    """
    p[0] = Node('FUN_EXP', [p[3], p[4]])


def p_FUN_NAME(p):
    """
    FUN_NAME : ID
    """
    p[0] = Node('FUN_NAME', [p[1]])


def p_FUN_IDs(p):
    """
    FUN_IDs : LPAREN VARIABLES RPAREN
    """
    p[0] = Node('FUN_IDs', [p[2]])


def p_FUN_BODY(p):
    """
    FUN_BODY : EXP
    """
    p[0] = Node('FUN_BODY', [p[1]])


def p_PARAM(p):
    """
    PARAM : EXP
    """
    p[0] = Node('PARAM', [p[1]])


def p_PARAMS(p):
    """
    PARAMS : PARAM PARAMS
           | empty
    """
    if len(p) == 3:
        p[0] = Node('PARAMS', [p[1], p[2]])
    else:
        p[0] = Node('NULL')


def p_FUN_CALL(p):
    """
    FUN_CALL : LPAREN FUN_EXP PARAMS RPAREN
             | LPAREN FUN_NAME PARAMS RPAREN
    """
    if p[2].type == 'FUN_EXP':
        p[0] = Node('FUN_CALL_ANONYMOUS', [p[2], p[3]])
    else:
        p[0] = Node('FUN_CALL_DEFINED', [p[2], p[3]])


def p_IF_EXP(p):
    """
    IF_EXP : LPAREN IF TEST_EXP THAN_EXP ELSE_EXP RPAREN
    """
    p[0] = Node('IF_EXP', [p[3], p[4], p[5]])


def p_TEST_EXP(p):
    """
    TEST_EXP : EXP
    """
    p[0] = Node('TEST_EXP', [p[1]])


def p_THAN_EXP(p):
    """
    THAN_EXP : EXP
    """
    p[0] = Node('THAN_EXP', [p[1]])


def p_ELSE_EXP(p):
    """
    ELSE_EXP : EXP
    """
    p[0] = Node('ELSE_EXP', [p[1]])


def p_empty(p):
    """
    empty :
    """
    pass


def p_error(p):
    global IS_VALID_SYNTAX
    IS_VALID_SYNTAX = False
    if IS_DEBUG:
        print(f'Syntax error at {p.value!r}')


parser = yacc()
ast = parser.parse(data)
if IS_VALID_SYNTAX and IS_DEBUG:
    print("AST:")
    print(ast)
    print('---' * 10)


def bfs(root: Node):
    q = deque([root])
    while q:
        for _ in range(len(q)):
            node = q.popleft()
            print(f'{node.type}:{node.value}', end=' ')
            for child in node.children:
                q.append(child)
        print()


if IS_VALID_SYNTAX and IS_DEBUG:
    print("AST BFS:")
    bfs(ast)
    print('---' * 10)


# --- Interpreter ---

class Function:
    def __init__(self, name, parm_list=[], arg_list=[], parm_dict={}, fun_exp=None):
        self.name = name
        self.parm_list = parm_list
        self.arg_list = arg_list
        self.parm_dict = parm_dict
        self.fun_exp = fun_exp
        self.is_anonymous = self.name == '_'
        self.caller = None

    def reset_parameters(self):
        self.parm_list.clear()
        self.arg_list.clear()
        self.parm_dict.clear()


opr_stack = []
# TODO: 應付遞迴或是嵌套函式的情況
fun_stack: list[Function] = []
variable_dict = defaultdict()
function_dict = defaultdict()
# NORMAL: 普通變數
# FUNCTION_ANONYMOUS: 匿名函式取得參數
# FUNCTION_DEFINED: 函式取得參數
# VARIABLE_STATUS = "NORMAL"
status_stack = []
# 用來記錄函式的參數與引數的對應，加速遞迴函式的執行
fun_param_memo = defaultdict()


def travel_ast(cur: Node):
    # global VARIABLE_STATUS
    if cur.type == 'STMTS':
        travel_ast(cur.children[0])
        travel_ast(cur.children[1])
    elif cur.type == 'PLUS':
        opr_stack.append('+')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 + exp2
        opr_stack.pop()
        return res
    elif cur.type == 'MINUS':
        opr_stack.append('-')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 - exp2
        opr_stack.pop()
        return res
    elif cur.type == 'MUL':
        opr_stack.append('*')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 * exp2
        opr_stack.pop()
        return res
    elif cur.type == 'DIV':
        opr_stack.append('/')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 // exp2
        opr_stack.pop()
        return res
    elif cur.type == 'MOD':
        opr_stack.append('%')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 % exp2
        opr_stack.pop()
        return res
    elif cur.type == 'GREATER':
        opr_stack.append('>')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 > exp2
        opr_stack.pop()
        return res
    elif cur.type == 'LESS':
        opr_stack.append('<')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 < exp2
        opr_stack.pop()
        return res
    elif cur.type == 'EQUAL':
        opr_stack.append('=')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 == exp2
        opr_stack.pop()
        return res
    elif cur.type == 'AND':
        opr_stack.append('and')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 and exp2
        opr_stack.pop()
        return res
    elif cur.type == 'OR':
        opr_stack.append('or')
        exp1 = travel_ast(cur.children[0])
        exp2 = travel_ast(cur.children[1])
        if type(exp1) is not type(exp2):
            raise TypeError
        res = exp1 or exp2
        opr_stack.pop()
        return res
    elif cur.type == 'NOT':
        opr_stack.append('not')
        exp1 = travel_ast(cur.children[0])
        if type(exp1) is not bool:
            raise TypeError
        res = not exp1
        opr_stack.pop()
        return res
    elif cur.type == 'PRINT_NUM':
        res = travel_ast(cur.children[0])
        if type(res) is not int:
            raise TypeError
        print(res)
    elif cur.type == 'PRINT_BOOL':
        res = travel_ast(cur.children[0])
        if type(res) is not bool:
            raise TypeError
        if res:
            print('#t')
        else:
            print('#f')
    elif cur.type == 'NUMBER':
        return cur.value
    elif cur.type == 'BOOL':
        return cur.value
    elif cur.type == 'EXPS':
        exp1 = travel_ast(cur.children[0])
        exp2 = None
        if opr_stack[-1] != 'not':
            exp2 = travel_ast(cur.children[1])
            if type(exp1) is not type(exp2):
                raise TypeError
        if opr_stack[-1] == '+':
            return exp1 + exp2
        elif opr_stack[-1] == '-':
            return exp1 - exp2
        elif opr_stack[-1] == '*':
            return exp1 * exp2
        elif opr_stack[-1] == '/':
            return exp1 // exp2
        elif opr_stack[-1] == '%':
            return exp1 % exp2
        elif opr_stack[-1] == '>':
            return exp1 > exp2
        elif opr_stack[-1] == '<':
            return exp1 < exp2
        elif opr_stack[-1] == '=':
            return exp1 == exp2
        elif opr_stack[-1] == 'and':
            return exp1 and exp2
        elif opr_stack[-1] == 'or':
            return exp1 or exp2
        elif opr_stack[-1] == 'not':
            if type(exp1) is not bool:
                raise TypeError
            return not exp1
    elif cur.type == 'IF_EXP':
        # ast tree: IF_EXP
        #    TEST_EXP THAN_EXP ELSE_EXP
        if travel_ast(cur.children[0]):
            return travel_ast(cur.children[1])
        else:
            return travel_ast(cur.children[2])
    elif cur.type == 'TEST_EXP':
        # ast tree: TEST_EXP->EXP
        res = travel_ast(cur.children[0])
        if type(res) is not bool:
            raise TypeError
        return res
    elif cur.type == 'THAN_EXP':
        # ast tree: THAN_EXP->EXP
        return travel_ast(cur.children[0])
    elif cur.type == 'ELSE_EXP':
        # ast tree: ELSE_EXP->EXP
        return travel_ast(cur.children[0])
    elif cur.type == 'DEF':
        # ast tree: DEF->VARIABLE->ID
        # 直接從 DEF 找到 ID
        if cur.children[0].type == 'VARIABLE':
            # ast tree: DEF->VARIABLE->ID->EXP
            # 變數定義
            variable_dict[cur.children[0].children[0].value] = travel_ast(cur.children[1])
        elif cur.children[0].type == 'FUN_NAME':
            # ast tree: DEF->FUN_NAME->ID
            # 函式定義
            # 由名字綁定一個Function物件，其中包含函式名稱、參數、引數、函式表達式(FUN_EXP)
            new_fun = Function(cur.children[0].children[0].value, [], [], {}, cur.children[1])
            function_dict[cur.children[0].children[0].value] = new_fun
    elif cur.type == 'VARIABLE':
        # ast tree: VARIABLE->ID
        # 從 VARIABLE 找到 ID
        # 這裡要注意，如果是函式的參數，就不要從 variable_dict 找，而是從 parm_dict 找
        if not status_stack:
            status = "NORMAL"
        else:
            status = status_stack[-1]
        variable_name = cur.children[0].value
        if status == "NORMAL":
            return variable_dict[variable_name]
        elif status == "FUNCTION_ANONYMOUS":
            return fun_stack[-1].parm_dict[variable_name]
        elif status == "FUNCTION_DEFINED":
            param_cnt = len(fun_stack[-1].parm_list)
            if param_cnt == 0:
                # 如果是零個參數，就從 variable_dict 找
                return variable_dict[variable_name]
            elif param_cnt == 1:
                if variable_name in fun_stack[-1].parm_dict:
                    return fun_stack[-1].parm_dict[variable_name]
                elif fun_stack[-1].caller and variable_name in fun_stack[-1].caller.parm_dict:
                    return fun_stack[-1].caller.parm_dict[variable_name]
                else:
                    # 如果都沒找到，就從 variable_dict 找，最終選擇
                    return variable_dict[cur.children[0].value]
            else:
                if fun_stack[-1].caller and variable_name in fun_stack[-1].caller.parm_dict:
                    return fun_stack[-1].caller.parm_dict[variable_name]
                elif variable_name in fun_stack[-1].parm_dict:
                    return fun_stack[-1].parm_dict[variable_name]
                else:
                    # 如果都沒找到，就從 variable_dict 找，最終選擇
                    return variable_dict[cur.children[0].value]
    elif cur.type == 'FUN_CALL_ANONYMOUS':
        # 匿名函式初始化，但這樣寫並沒有考慮嵌套函式的情況
        VARIABLE_STATUS = "FUNCTION_ANONYMOUS"
        status_stack.append(VARIABLE_STATUS)
        fun_exp = cur.children[0]
        fun_to_call = Function('_', [], [], {}, fun_exp)
        fun_stack.append(fun_to_call)
        # ast tree: FUN_CALL_ANONYMOUS->FUN_EXP
        # 蒐集參數
        travel_ast(fun_exp)
        # ast tree: FUN_CALL_ANONYMOUS->PARAMS
        # 蒐集引數
        travel_ast(cur.children[1])
        # Binding 參數與引數綁定
        for i in range(len(fun_to_call.parm_list)):
            fun_to_call.parm_dict[fun_to_call.parm_list[i]] = fun_to_call.arg_list[i]
        # ast tree: FUN_CALL_ANONYMOUS->FUN_EXP->FUN_BODY
        # 函式本體
        fun_body = fun_to_call.fun_exp.children[1]
        result = travel_ast(fun_body)
        # VARIABLE_STATUS = "NORMAL"
        fun_stack.pop()
        status_stack.pop()
        return result
    elif cur.type == 'FUN_EXP':
        # ast tree: FUN_EXP->FUN_IDs
        # 蒐集參數
        travel_ast(cur.children[0])
    elif cur.type == 'FUN_IDs':
        # ast tree: FUN_IDs->VARIABLES
        # 蒐集參數
        travel_ast(cur.children[0])
    elif cur.type == 'FUN_BODY':
        # ast tree: FUN_BODY->EXP
        # 函式本體
        return travel_ast(cur.children[0])
    elif cur.type == 'PARAMS':
        # 只有函式呼叫會出現的節點
        if cur.children[0].type == 'NULL':
            # ast tree: PARAMS->NULL
            # 代表沒有引數
            pass
        elif cur.children[0].type == 'PARAM':
            # ast tree: PARAMS->PARAM->EXP(could be FUN_CALL)
            # 蒐集引數
            fun_stack[-1].arg_list.append(travel_ast(cur.children[0].children[0]))
        if cur.children[1].type == 'PARAMS':
            # ast tree: PARAMS->PARAMS->PARAM->EXP
            # 蒐集更多引數
            travel_ast(cur.children[1])
    elif cur.type == 'PARAM':
        # 因為會直接從PARAMS->PARAM->EXP，所以這裡不會被執行到
        pass
    elif cur.type == 'VARIABLES':
        # 只有函式呼叫會出現的節點
        if cur.children[0].type == 'NULL':
            # ast tree: VARIABLES->NULL
            # 代表沒有參數
            pass
        elif cur.children[0].type == 'VARIABLE':
            # ast tree: VARIABLES->VARIABLE->ID
            # 蒐集參數
            fun_stack[-1].parm_list.append(cur.children[0].children[0].value)
        if cur.children[1].type == 'VARIABLES':
            # ast tree: VARIABLES->VARIABLES->VARIABLE->ID
            # 蒐集更多參數
            travel_ast(cur.children[1])
    elif cur.type == 'FUN_CALL_DEFINED':
        # TODO: 應付遞迴或是嵌套函式的情況
        VARIABLE_STATUS = "FUNCTION_DEFINED"
        status_stack.append(VARIABLE_STATUS)
        # ast tree: FUN_CALL_DEFINED->FUN_NAME->ID
        fun_name = cur.children[0].children[0].value
        # 找到對應的Function物件
        if fun_stack and fun_name == fun_stack[-1].name:
            # 是遞迴函式，但這樣判斷並不準確
            fun_to_call = deepcopy(fun_stack[-1])
            fun_to_call.parm_list.clear()
            fun_to_call.arg_list.clear()
            fun_to_call.caller = fun_stack[-1]
        else:
            fun_to_call = function_dict[fun_name]
            fun_to_call.parm_list.clear()
            fun_to_call.arg_list.clear()
            if fun_stack:
                fun_to_call.caller = fun_stack[-1]
            else:
                fun_to_call.caller = None
        fun_stack.append(fun_to_call)
        fun_exp = fun_to_call.fun_exp
        # ast tree: FUN_EXP->[FUN_IDs]
        # 蒐集參數
        travel_ast(fun_exp)
        # ast tree: FUN_CALL_DEFINED->PARAMS
        # 蒐集引數
        travel_ast(cur.children[1])
        # Binding 參數與引數綁定
        for i in range(len(fun_to_call.parm_list)):
            fun_to_call.parm_dict[fun_to_call.parm_list[i]] = fun_to_call.arg_list[i]
        # ast tree: FUN_EXP->FUN_BODY
        # 函式本體
        fun_body = fun_to_call.fun_exp.children[1]
        if (fun_name, tuple(fun_to_call.arg_list)) in fun_param_memo:
            result = fun_param_memo[(fun_name, tuple(fun_to_call.arg_list))]
        else:
            result = travel_ast(fun_body)
            fun_param_memo[(fun_name, tuple(fun_to_call.arg_list))] = result
        # print(f'{fun_name}({fun_to_call.parm_dict})={result}')
        # VARIABLE_STATUS = "NORMAL"
        fun_stack.pop()
        status_stack.pop()
        return result
    elif cur.type == 'FUN_NAME':
        # 因為會直接從FUN_CALL_DEFINED->FUN_NAME->ID，所以這裡不會被執行到
        pass
    elif cur.type == 'NULL':
        pass


if IS_VALID_SYNTAX and IS_DEBUG:
    print("Result:")

if IS_VALID_SYNTAX:
    try:
        travel_ast(ast)
    except TypeError:
        print("Type error!")
    if IS_DEBUG:
        print('---' * 10)
        print("Variable Dictionary:")
        print(variable_dict)
        print("Function Dictionary:")
        print(function_dict)
        print("Function Stack:")
        print(fun_stack)
        print("Status Stack:")
        print(status_stack)
else:
    print("syntax error")


# --- Visualize AST ---
def add_nodes_edges(graph, parent_node, level, pos, sibling_distance=10., vert_gap=0.4, xcenter=0.5):
    if parent_node is not None:
        current_type = f"{parent_node.type}_{parent_node.id}\n[{parent_node.value}]"
        if current_type not in pos:
            pos[current_type] = (xcenter, 1 - level * vert_gap)
            graph.add_node(current_type, pos=(xcenter, 1 - level * vert_gap))

        xcenter -= sibling_distance / 2

        for child in parent_node.children:
            xcenter += sibling_distance
            child_type = f"{child.type}_{child.id}\n[{child.value}]"
            pos[child_type] = (xcenter, 1 - (level + 1) * vert_gap)
            graph.add_edge(current_type, child_type)
            pos, xcenter = add_nodes_edges(graph, child, level + 1, pos, sibling_distance=sibling_distance,
                                           vert_gap=vert_gap, xcenter=xcenter)

    return pos, xcenter


def plot_tree(root):
    graph = nx.Graph()
    pos = {}
    pos, _ = add_nodes_edges(graph, root, 0, pos, sibling_distance=100., vert_gap=0.4, xcenter=0.5)
    nx.draw(graph, pos=pos, with_labels=True, font_weight='bold', node_size=700, node_color="skyblue", font_size=4)
    plt.show()


if IS_VALID_SYNTAX and IS_DEBUG:
    plot_tree(ast)
