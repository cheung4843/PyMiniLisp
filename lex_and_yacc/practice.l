%{
#include "practice.tab.h"
#include <string.h>


%}
%option noyywrap

separator \t|\n|\r|[ ]
letter [a-z]
digit [0-9]


%%
"print-num" {
    return PRINT_NUM;
}

"print-bool" {
    return PRINT_BOOL;
}

0|[1-9][0-9]*|\-[1-9][0-9]* { 
    yylval.rval.value = atoi(yytext);
    return NUMBER; 
    // ECHO;
}

\#t|\#f {
    if(strcmp(yytext,"#t") == 0 )
		yylval.rval.value = 1;
	else
	    yylval.rval.value = 0;
    return BOOL;
    // ECHO;
}

"+"|"-"|"*"|"/"|">"|"<"|"=" {
    return yytext[0];
}

"mod" {
    return MOD;
}

"and" {
    return AND;
}

"or" {
    return OR;
}

"not" {
    return NOT;
}

"define" {
    return DEF;
}

"fun" {
    return FUN;
}

"if" {
    return IF;
}

[a-z]([a-z]|[0-9]|\-)* {
    yylval.rval.var = strdup(yytext);
    return ID;
    // ECHO;
}

"("|")" {
    return yytext[0];
}

{separator} {
    // ECHO;
}


.|\n {
    // ECHO;
}

%%

// int main() {
//     yylex();
//     return 0;
// }