from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os.path


class RubyConan(ConanFile):
    name = "ruby"
    version = "2.5.1"
    license = "MIT"
    url = "https://www.ruby-lang.org/"
    description = "The Ruby Programming Language"
    settings = "os", "compiler", "build_type", "arch"
    extensions = (
        "bigdecimal",
        "cgi/escape",
        "continuation",
        "coverage",
        "date",
        "dbm",
        # "digest/bubblebabble",
        # "digest",
        # "digest/md5",
        # "digest/rmd160",
        # "digest/sha1",
        # "digest/sha2",
        "etc",
        "fcntl",
        "fiber",
        "fiddle",
        "gdbm",
        "io/console",
        "io/nonblock",
        "io/wait",
        "json",
        "json/generator",
        "json/parser",
        "nkf",
        "objspace",
        "openssl",
        "pathname",
        "psych",
        "pty",
        "racc/cparse",
        "rbconfig/sizeof",
        "readline",
        "ripper",
        "sdbm",
        "socket",
        # "stringio",
        "strscan",
        "syslog",
        "win32",
        "win32ole",
        "zlib",
    )
    options = dict({
        "shared": [True, False],
    }, **{"with_" + extension: [True, False] for extension in extensions})
    default_options = (
        "shared=False",
        "cygwin_installer:additional_packages=bison,ruby",
    ) + tuple("with_{}=False".format(extension) for extension in extensions)

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.settings.compiler == "Visual Studio":
            del self.settings.build_type

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio":
            raise Exception("Only Visual Studio supported on Windows")

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("cygwin_installer/2.9.0@bincrafters/stable")

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.11@conan/stable")

    def source(self):
        self.run("git clone https://github.com/ruby/ruby.git -b v{} --depth 1"
                 .format(self.version.replace(".", "_")))

    def build(self):
        without_ext = (tuple(extension for extension in self.extensions
                             if not getattr(self.options, "with_" + extension)))

        with tools.chdir("ruby"):
            if self.settings.compiler == "Visual Studio":
                cygwin_bin = self.deps_env_info["cygwin_installer"].CYGWIN_BIN
                with tools.environment_append({"PATH": [cygwin_bin],
                                               "INCLUDE": self.deps_cpp_info.include_paths,
                                               "LIB": self.deps_cpp_info.lib_paths}):
                    with tools.vcvars(self.settings):
                        if self.settings.arch == "x86":
                            target = "i386-mswin32"
                        elif self.settings.arch == "x86_64":
                            target = "x64-mswin64"
                        else:
                            raise Exception("Invalid arch")
                        self.run("{} --prefix={} --target={} --without-ext=\"{},\" --disable-install-doc".format(
                            os.path.join("win32", "configure.bat"),
                            self.package_folder,
                            target,
                            ",".join(without_ext)))
                        self.run("nmake")
                        self.run("nmake install")
            else:
                autotools = AutoToolsBuildEnvironment(self)
                self.run("autoconf")
                autotools.configure(args=[
                    "--with-out-ext=" + ",".join(without_ext),
                    "--disable-install-rdoc",
                    "--without-gmp",
                ])
                autotools.make()
                autotools.install()

    def package(self):
        pass

    def package_info(self):
        includedir = os.path.join("include", "ruby-2.5.0")
        self.cpp_info.includedirs = [includedir]
        if self.settings.os == "Windows":
            # Find include config dir
            includename = None
            for f in os.listdir(os.path.join(self.package_folder, includedir)):
                if "mswin" in f:
                    includename = f
                    break
            if not includename:
                raise Exception("Could not find Ruby config dir")
            # Find library
            libname = None
            for f in os.listdir(os.path.join(self.package_folder, "lib")):
                name, ext = os.path.splitext(f)
                if ext == ".lib":
                    if self.options.shared:
                        if not name.endswith("-static"):
                            libname = name
                            break
                    else:
                        if name.endswith("-static"):
                            libname = name
                            break
            if not libname:
                raise Exception("Could not find Ruby lib")
            self.cpp_info.libs = [libname, "ws2_32", "Iphlpapi", "Shlwapi", "Dbghelp"]
        else:
            if self.settings.os == "Linux":
                includename = "{}-linux".format(self.settings.arch)
            else:
                raise Exception("Could not find Ruby config dir")
            self.cpp_info.libs = tools.collect_libs(self) + ["dl", "crypt", "m"]
            self.cpp_info.cppflags = ["-pthread"]
        self.cpp_info.includedirs.append(os.path.join(includedir, includename))
