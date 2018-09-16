#include <iostream>
#include <ruby.h>

int main() {
    int argc = 0;
    char **argv = 0;
    ruby_sysinit(&argc, &argv);

    ruby_setup();

    int state;
    rb_eval_string_protect("puts 'Hello, world!'", &state);

    ruby_cleanup(0);

    return state;
}
