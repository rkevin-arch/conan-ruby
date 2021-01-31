#include <iostream>
#include <ruby.h>


int main() {
    int argc = 0;
    char **argv = 0;
    ruby_sysinit(&argc, &argv);

    ruby_setup();

    int state;
    // for linux
    rb_eval_string_protect(
        "if RUBY_PLATFORM =~ /linux/\n"
        "    $LOAD_PATH.unshift(File.join(Dir.pwd, '..', 'lib', 'ruby'))\n"
        "    $LOAD_PATH.unshift(File.join(Dir.pwd, '..', 'lib', 'ruby', RUBY_PLATFORM))\n"
        "else\n"
        "    $LOAD_PATH.unshift(File.join(Dir.pwd, 'lib', 'ruby'))\n"
        "    $LOAD_PATH.unshift(File.join(Dir.pwd, 'lib', 'ruby', RUBY_PLATFORM))\n"
        "end", &state);

    if(state) {
        // blatantly copied from mkxp's binding-mri/binding-mri.cpp, showExc
        VALUE exc = rb_errinfo();
        VALUE bt = rb_funcall2(exc, rb_intern("backtrace"), 0, NULL);
        VALUE bt0 = rb_ary_entry(bt, 0);
        VALUE msg = rb_funcall2(exc, rb_intern("message"), 0, NULL);
        VALUE ds = rb_sprintf("%" PRIsVALUE ": %" PRIsVALUE "\n", bt0, exc);
        printf("%s", StringValueCStr(ds));
    }
    rb_eval_string_protect("puts Encoding.aliases", &state);
    rb_eval_string_protect("require 'enc/encdb.so'; require 'enc/trans/transdb.so'; require 'net/http'; puts Net::HTTP::get(URI('https://example.com'))", &state);
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
