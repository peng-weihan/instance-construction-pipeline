#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--help") == 0) { puts("bytecopy: copy stdin bytes to stdout"); return 0; }
    if (argc != 1) { fputs("unknown option\n", stderr); return 2; }
    int c;
    while ((c = getchar()) != EOF) putchar(c);
    return ferror(stdin) ? 3 : 0;
}
