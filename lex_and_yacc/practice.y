%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if YYDEBUG == 1
    extern yydebug;
    yydebug = 1;
#endif


#define TRUE 1
#define FALSE 0

int yylex();
void yyerror(const char *message);


int num_arr[100];
int top = 0;
char parm_arr[100];
int parm_top = 0;

typedef struct {
    char name[256];
    int value;
} Symbol;

Symbol symbol_table[100];
int symbol_count = 0;

int get_value(char *name) {
    for (int i = 0; i < symbol_count; ++i) {
        if (strcmp(symbol_table[i].name, name) == 0) {
            return symbol_table[i].value;
        }
    }
    fprintf(stderr, "Error: Variable %s not found\n", name);
    return -1;
}

void set_value(char *name, int value) {
    for (int i = 0; i < symbol_count; ++i) {
        if (strcmp(symbol_table[i].name, name) == 0) {
            symbol_table[i].value = value;
            return;
        }
    }
    if (symbol_count < sizeof(symbol_table) / sizeof(symbol_table[0])) {
        strcpy(symbol_table[symbol_count].name, name);
        symbol_table[symbol_count].value = value;
        symbol_count++;
    } else {
        fprintf(stderr, "Error: Symbol table overflow\n");
        return;
    }
}

%}

%code requires {
	
    typedef struct e {
        char type;
		int value;
		char* var;
    } E;
}


%union{
	int ival;
	int bval;
	char* sval;
	E rval;
}

%token<rval> NUMBER BOOL ID
%token MOD AND OR NOT DEF IF FUN
%token PRINT_NUM PRINT_BOOL
%type<rval> EXP VARIABLE NUM-OP LOGICAL-OP FUN-EXP FUN-CALL IF-EXP
%type<rval> TEST-EXP THAN-EXP ELSE-EXP
%type<rval> EXPS

%left '+' '-'
%left '*' '/' 

%%
PROGRAM		: STMTS { 
				printf("Accepted\n");
			}
			;
STMTS		: STMT STMTS
			| STMT
			;
STMT		: EXP 
			| PRINT-STMT
			| DEF-STMT
			;
PRINT-STMT	: '(' PRINT_NUM EXP ')' {
				printf("PRINT_NUM: %d\n", $3.value);

			}
			| '(' PRINT_BOOL EXP ')' {
				if($3.value){
					printf("#t\n");
				}else{
					printf("#f\n");
				}
				
			}
			;
EXPS		: EXP EXPS {
				num_arr[top] = $2.value;
				top++;
			}
			| EXP {
				$$.value = $1.value;
			}
			;
EXP			: BOOL {
				$$.type = 'B';
				$$.value = $1.value;
				// printf("%d\n", $$.value);
			}
			| NUMBER {
				$$.type = 'N';
				$$.value = $1.value;
				// printf("NUM:%d\n", $$.value);
			}
			| VARIABLE {
				$$.value = get_value($1.var);
			}
			| NUM-OP
			| LOGICAL-OP
			| FUN-EXP
			| FUN-CALL
			| IF-EXP
			;
NUM-OP		: '(' '+' EXPS ')' {
				int res = $3.value;
				for(int i=0;i<top;i++){
					res += num_arr[i];
				}
				$$.value = res;
				top = 0;
				// printf("%d\n", $$.value);
			}
			| '(' '-' EXP EXP ')' {
				$$.value = $3.value - $4.value;
				// printf("%d\n", $$.value);
			}
			| '(' '*' EXPS ')' {
				int res = $3.value;
				for(int i=0;i<top;i++){
					res *= num_arr[i];
				}
				$$.value = res;
				top = 0;
			}
			| '(' '/' EXP EXP ')' {
				$$.value = $3.value / $4.value;
			}
			| '(' MOD EXP EXP ')' {
				$$.value = $3.value % $4.value;

			}
			| '(' '>' EXP EXP ')' {
				$$.type = 'B';
				$$.value = $3.value > $4.value;
			}
			| '(' '<' EXP EXP ')' {
				$$.type = 'B';
				$$.value = $3.value < $4.value;
			}
			| '(' '=' EXPS ')' {
				$$.type = 'B';
				int res = $3.value == num_arr[0];
				for(int i=1;i<top;i++){
					if(num_arr[i] != num_arr[i - 1]){
						res = 0;
						break;
					}
				}
				$$.value = res;
				top = 0;
			}
			;
LOGICAL-OP	: '(' AND EXPS ')' {
				$$.type = 'B';
				int res = $3.value;
				// printf("%d ", res);
				for(int i=0;i<top;i++){
					if(num_arr[i] == 0){
						res = 0;
						break;
					}
				}
				$$.value = res;
				top = 0;
			}
			| '(' OR EXPS ')' {
				$$.type = 'B';
				int res = $3.value;
				for(int i=0;i<top;i++){
					if(num_arr[i]){
						res = 1;
						break;
					}
				}
				$$.value = res;
				top = 0;

			}
			| '(' NOT EXP ')' {
				$$.type = 'B';
				$$.value = !$3.value;
			}
			;
DEF-STMT	: '(' DEF VARIABLE EXP ')' {
				set_value($3.var, $4.value);
				// printf("%s:%d", $3.var, get_value($3.var));
			}
			;
VARIABLES	: VARIABLES VARIABLE
			| // lambda
			;
VARIABLE	: ID
			;
FUN-EXP		: '(' FUN FUN-IDs FUN-BODY ')' {
				printf("FUNCTION\n");

			}
			; 
FUN-IDs		: '(' VARIABLES ')'
			;
FUN-BODY	: EXP
			;
FUN-CALL	: '(' FUN-EXP PARAMS ')' {
				printf("FUNCTION CALL 1\n");

			}
			| '(' FUN-NAME PARAMS ')' {
				printf("FUNCTION CALL 2\n");
			}
			;
PARAMS		: PARAM PARAMS {

			}
			| // lambda
			;
PARAM		: EXP {

			}
			;
FUN-NAME	: ID
			;
IF-EXP		: '(' IF TEST-EXP THAN-EXP ELSE-EXP ')' {
				if($3.value){
					$$.value = $4.value;
				}else{
					$$.value = $5.value;
				}
			}
			;
TEST-EXP	: EXP
			;
THAN-EXP	: EXP
			;
ELSE-EXP	: EXP
			;
%%

void yyerror (const char *message)
{
	/** This function is called when there is a syntax error **/
	printf("Syntax Error\n");
}

int main()
{

	/** You can write any code in main function **/
	yyparse();
	
	return 0;
}