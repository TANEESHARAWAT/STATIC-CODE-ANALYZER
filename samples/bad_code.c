/*
 * bad_code.c — Sample file with intentional violations across all compiler phases.
 * Use this to test the static analyzer.
 *
 * Run: python main.py samples/bad_code.c
 * Run: python main.py samples/bad_code.c --ai
 */

#include <stdio.h>
#include <stdlib.h>
/* Missing: #include <string.h> */

/* ─── LEXICAL ERRORS ─────────────────────────────── */

/* LEX002: invalid escape sequence */
void lexical_demo() {
    char *msg = "Hello \q World";   /* \q is not a valid escape */
    printf("%s\n", msg);
}

/* ─── SYNTAX ERRORS ──────────────────────────────── */

/* SYN003: unmatched brace will be caught */
/* SYN002: missing semicolon */
void syntax_demo() {
    int x = 5
    int y = 10;
    printf("%d\n", x + y);
}

/* ─── SEMANTIC ERRORS ────────────────────────────── */

/* SEM001: function name not snake_case */
int BadFunctionName(int a) {
    return a + 1;
}

/* SEM002: too many parameters */
int too_many_params(int a, int b, int c, int d, int e, int f) {
    return a + b + c + d + e + f;
}

/* SEM003: use of gets() */
void read_input_unsafe() {
    char buf[64];
    gets(buf);
    printf("%s\n", buf);
}

/* SEM004: use of strcpy */
void copy_string(const char *src) {
    char dest[64];
    strcpy(dest, src);
    printf("%s\n", dest);
}

/* SEM005: magic numbers */
int compute(int x) {
    return x * 42 + 100;
}

/* SEM006: unused variable */
void unused_var_demo() {
    int result = 0;
    int unused_counter = 5;
    result = 10;
    printf("%d\n", result);
}

/* SEM007: non-void function without return */
int missing_return(int x) {
    if (x > 0) {
        printf("positive\n");
    }
    /* no return here */
}

/* SEM008: empty else block */
void empty_else(int flag) {
    if (flag) {
        printf("flag is set\n");
    } else {}
}

/* SEM009: scanf with %s and no width */
void unsafe_scanf() {
    char name[32];
    scanf("%s", name);
}

/* SEM010: malloc not checked for NULL */
void unchecked_malloc() {
    int *arr = malloc(100 * sizeof(int));
    arr[0] = 1;
    free(arr);
}

/* SEM012: division by zero */
void divide_by_zero() {
    int x = 10 / 0;
    printf("%d\n", x);
}

/* SEM013: assignment in condition */
void assign_in_condition(int val) {
    if (val = 5) {
        printf("got 5\n");
    }
}

/* SEM014: format injection */
void format_injection(char *user_input) {
    printf(user_input);
}

/* SEM015: dead code after return */
int dead_code_demo(int x) {
    return x * 2;
    printf("this never runs\n");
    x = x + 1;
}

/* SEM016: array out of bounds */
void array_oob() {
    int arr[5];
    arr[5] = 99;   /* index 5 in a size-5 array */
    arr[10] = 88;  /* way out of bounds */
}

/* SEM017: infinite loop without break */
void infinite_loop() {
    while (1) {
        printf("spinning forever\n");
    }
}

/* SEM018: dangerous function */
void dangerous_funcs(char *src) {
    char buf[100];
    sprintf(buf, src);
    strcat(buf, " extra");
}

/* SEM024: double free */
void double_free_demo() {
    int *p = malloc(sizeof(int));
    if (p == NULL) return;
    *p = 42;
    free(p);
    free(p);   /* double free! */
}

/* ─── CODEGEN HINTS ──────────────────────────────── */

/* CGN001: not all paths return a value */
int partial_return(int x) {
    if (x > 100) {
        return x;
    }
    /* falls off end without return */
}

/* CGN002: ignoring return value of fopen */
void ignore_return_value() {
    fopen("data.txt", "r");   /* return value ignored */
}

/* CGN003: pointer param never written to — should be const */
void should_be_const(int *data, int len) {
    for (int i = 0; i < len; i++) {
        printf("%d\n", data[i]);
    }
}
