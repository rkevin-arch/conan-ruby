#include <iostream>
#include <ruby.h>

extern "C" {
    RUBY_EXTERN void ruby_init_ext(const char *name, void (*init)(void));
    RUBY_EXTERN void Init_socket(void);
}

int main() {
    int argc = 0;
    char **argv = 0;
    ruby_sysinit(&argc, &argv);

    ruby_setup();

    ruby_init_ext("socket.so", Init_socket);

    int state;
    rb_eval_string_protect("require 'socket'\nputs TCPSocket", &state);

    if(state) {
        // blatantly copied from mkxp's binding-mri/binding-mri.cpp, showExc
        VALUE exc = rb_errinfo();
        VALUE bt = rb_funcall2(exc, rb_intern("backtrace"), 0, NULL);
        VALUE bt0 = rb_ary_entry(bt, 0);
        VALUE msg = rb_funcall2(exc, rb_intern("message"), 0, NULL);
        VALUE ds = rb_sprintf("%" PRIsVALUE ": %" PRIsVALUE "\n", bt0, exc);
        printf("%s", StringValueCStr(ds));
    }

    ruby_cleanup(0);

    return state;
}
