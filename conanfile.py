from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanException
import os.path


class RubyConan(ConanFile):
    name = "ruby"
    version = "2.5.3"
    description = "The Ruby Programming Language"
    topics = ("conan", "ruby")
    url = "https://github.com/elizagamedev/conan-ruby"
    homepage = "https://www.ruby-lang.org"
    author = "Eliza Velasquez"
    license = "MIT"
    settings = "os", "compiler", "build_type", "arch"
    extensions = (
        "dbm",
        "gdbm",
        "openssl",
        "pty",
        "readline",
        "syslog",
    )
    options = {"with_" + extension: [True, False] for extension in extensions}
    default_options = {"with_" + extension: False for extension in extensions}

    _source_subfolder = "ruby-{}".format(version)

    build_requires = "ruby_installer/2.5.5@bincrafters/stable"

    def configure(self):
        del self.settings.compiler.libcxx

    def build_requirements(self):
        if tools.os_info.is_windows:
            self.build_requires("msys2_installer/20161025@bincrafters/stable")

    def requirements(self):
        if self.options.with_openssl:
            self.requires("OpenSSL/1.1.0i@conan/stable")

    def source(self):
        tools.get("https://cache.ruby-lang.org/pub/ruby/{}/{}.tar.gz".format(
            self.version.rpartition(".")[0],
            self._source_subfolder))

    def build_configure(self):
        without_ext = (tuple(extension for extension in self.extensions
                             if not getattr(self.options, "with_" + extension)))

        with tools.chdir(self._source_subfolder):
            if self.settings.compiler == "Visual Studio":
                with tools.environment_append({"INCLUDE": self.deps_cpp_info.include_paths,
                                               "LIB": self.deps_cpp_info.lib_paths}):
                    if self.settings.arch == "x86":
                        target = "i686-mswin32"
                    elif self.settings.arch == "x86_64":
                        target = "x64-mswin64"
                    else:
                        raise Exception("Invalid arch")
                    self.run("{} --prefix={} --target={} --without-ext=\"{},\" --disable-install-doc".format(
                        os.path.join("win32", "configure.bat"),
                        self.package_folder,
                        target,
                        ",".join(without_ext)))

                    # Patch in runtime settings
                    def define(line):
                        tools.replace_in_file(
                            "Makefile",
                            "CC = cl -nologo",
                            "CC = cl -nologo\n" + line)
                    define("RUNTIMEFLAG = -{}".format(self.settings.compiler.runtime))
                    if self.settings.build_type == "Debug":
                        define("COMPILERFLAG = -Zi")
                        define("OPTFLAGS = -Od -Ob0")

                    self.run("nmake")
                    self.run("nmake install")
            else:
                win_bash = tools.os_info.is_windows
                autotools = AutoToolsBuildEnvironment(self, win_bash=win_bash)
                # Remove our libs; Ruby doesn't like Conan's help
                autotools.libs = []
                if self.settings.compiler == "clang":
                    autotools.link_flags.append("--rtlib=compiler-rt")

                args = [
                    "--with-out-ext=" + ",".join(without_ext),
                    "--disable-install-doc",
                    "--without-gmp",
                    "--enable-shared",
                ]

                autotools.configure(args=args)
                autotools.make()
                autotools.install()

    def build(self):
        if tools.os_info.is_windows:
            msys_bin = self.deps_env_info["msys2_installer"].MSYS_BIN
            # Make sure that Ruby is first in the path order
            path = self.deps_env_info["ruby_installer"].path + [msys_bin]
            with tools.environment_append({"PATH": path,
                                           "CONAN_BASH_PATH": os.path.join(msys_bin, "bash.exe")}):
                if self.settings.compiler == "Visual Studio":
                    with tools.vcvars(self.settings):
                        self.build_configure()
                else:
                    self.build_configure()
        else:
            self.build_configure()

    def package_info(self):
        # Find correct lib (shared)
        libname = None
        for f in os.listdir("lib"):
            name, ext = os.path.splitext(f)
            if ext in (".so", ".lib", ".a", ".dylib"):
                if ext != ".lib" and name.startswith("lib"):
                    name = name[3:]
                if not name.endswith("-static"):
                    libname = name
                    break
        if not libname:
            raise ConanException("Could not find built shared library")
        self.cpp_info.libs = [libname]

        # Find include config dir
        includedir = os.path.join("include", "ruby-2.5.0")
        configdir = None
        for f in os.listdir(os.path.join(self.package_folder, includedir)):
            if "mswin" in f or "mingw" in f or "linux" in f or "darwin" in f:
                configdir = f
                break
        if not includedir:
            raise Exception("Could not find Ruby config dir")
        self.cpp_info.includedirs = [includedir,
                                     os.path.join(includedir, configdir)]
