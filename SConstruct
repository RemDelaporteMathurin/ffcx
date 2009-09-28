# -*- coding: utf-8 -*-
import os, sys, glob, re
from os.path     import join, isfile, isdir, getsize, sep, normpath, dirname, basename
from distutils   import sysconfig
from swig_config import configure_swig_env, get_status_output

# Make sure that we have a good scons-version
EnsureSConsVersion(0, 98, 5)

# Create a SCons Environment based on the main os environment
env = Environment(ENV=os.environ)

# UFC version number
ufc_file = open("src/ufc/ufc.h","r").read()
major = int(re.findall("UFC_VERSION_MAJOR ([0-9])",ufc_file)[0])
minor = int(re.findall("UFC_VERSION_MINOR ([0-9])",ufc_file)[0])
maintenance = int(re.findall("UFC_VERSION_MAINTENANCE ([0-9])",ufc_file)[0])

# Build the commandline options for SCons:
if env["PLATFORM"].startswith("win"):
    default_prefix = r"c:\local"
elif env["PLATFORM"] == "darwin":
    default_prefix = join(sep,"sw")
else:
    default_prefix = join(sep,"usr","local")

if env["PLATFORM"].startswith("win"):
    default_python_dir = os.path.join("$prefix", "Lib", "site-packages")
elif env["PLATFORM"] == "darwin":
    default_python_dir = os.path.join("$prefix", "lib", "python" + sysconfig.get_python_version(),"site-packages")
else:
    default_python_dir = sysconfig.get_python_lib(prefix="$prefix",plat_specific=True)

options = [
    # configurable options for installation:
    PathVariable("prefix", "Installation prefix", default_prefix, PathVariable.PathAccept),
    PathVariable("includeDir", "ufc.h installation directory",
               join("$prefix","include"), PathVariable.PathAccept),
    PathVariable("pythonModuleDir", "Python module installation directory", 
               default_python_dir, PathVariable.PathAccept),
    BoolVariable("enablePyUFC", "Compile and install the python extension module", "Yes"),
    PathVariable("pythonExtDir", "Python extension module installation directory",
               default_python_dir, PathVariable.PathAccept),
    PathVariable("boostDir", "Specify path to Boost", None),
    PathVariable("pkgConfDir", "Directory for installation of pkg-config files",
               join("$prefix","lib","pkgconfig"), PathVariable.PathAccept),
    BoolVariable("cleanOldUFC", "Clean any old installed UFC modules", "No"),
    BoolVariable("cacheOptions", "Cache command-line options for later invocations", "Yes"),
    PathVariable("DESTDIR", "Prepend DESTDIR to each installed target file",
               None, PathVariable.PathAccept),
    ]

# Set the options using any cached options
cache_file = "options.cache"
opts = Variables(cache_file, args=ARGUMENTS.copy())
opts.AddVariables(*options)
opts.Update(env)
cache_options = env.get("cacheOptions", False)
DESTDIR = env.get("DESTDIR")
if cache_options:
    del env["cacheOptions"] # Don't store this value
    if DESTDIR:
        del env["DESTDIR"]
    opts.Save(cache_file, env)
    # Restore cacheOptions
    env["cacheOptions"] = cache_options
    if DESTDIR:
        env["DESTDIR"] = DESTDIR

# Start building the message presented at the end of a simulation
end_message = "\n"

# Check for old ufc installation
old_ufc_modules = []
for p in sys.path:
    if isfile(join(p,"ufc","__init__.py")):
        old_ufc_modules.append(join(p,"ufc"))

# If not cleaning
if not env.GetOption("clean"):
    # Notify the user about that options from scons/options.cache are being used:
    if isfile(cache_file) and getsize(cache_file):
        print "Using options from options.cache"
    
    # Append end_message if old ufc module excists
    if old_ufc_modules:
        end_message +=  """
---------------------------------------------------------
*** Warning: Old ufc module

%s
  
still excists in installation path.
Try remove these files with:

    scons -c cleanOldUFC=Yes

Note that you may need to be root.
"""%("\n".join("    " + m for m in old_ufc_modules))

# Generate pkgconfig file
pkg_config_file = "ufc-%d.pc" % major
file = open(pkg_config_file, "w")
file.write("Name: UFC\n")
file.write("Version: %d.%d.%d\n" % (major, minor, maintenance))
file.write("Description: Unified Form-assembly Code\n")
file.write("Cflags: -I%s\n" % \
           repr(normpath(env.subst(env["includeDir"])))[1:-1])
file.close()

if env.get("DESTDIR"):
    install_prefix = os.path.join("$DESTDIR", "$prefix")
    tgts_dir = ["includeDir", "pythonModuleDir", "pythonExtDir", "pkgConfDir"]
    for tgt_dir in tgts_dir:
        env[tgt_dir] = env[tgt_dir].replace("$prefix", install_prefix)

# If necessary, replace site-packages with dist-packages when prefix is
# either /usr or /usr/local (hack for Python 2.6 on Debian/Ubuntu)
if env.subst("$prefix").rstrip("/") in ("/usr", "/usr/local") and \
       "dist-packages" in sysconfig.get_python_lib():
    for tgt_dir in ["pythonModuleDir", "pythonExtDir"]:
        env[tgt_dir] = env[tgt_dir].replace("site-packages", "dist-packages")
               
# Now generate the help text
env.Help(opts.GenerateHelpText(env))

# Set up installation targets
ufc_basename = join("src", "ufc", "ufc")
env.Install(env["pkgConfDir"],File(pkg_config_file))
env.Install(env["includeDir"],File(ufc_basename+".h"))
env.Install(join(env["pythonModuleDir"],"ufc_utils"),
            [File(f) for f in glob.glob(join("src","utils","python","ufc","*.py") )])

targets = [env["pkgConfDir"],env["pythonModuleDir"],env["includeDir"]]

# If compiling the extension module
if env["enablePyUFC"]:
    swig_env, message = configure_swig_env(env.Clone())
    end_message += message
    if swig_env["enablePyUFC"]:
        ufc_wrap, ufc_py = swig_env.CXXFile(target=ufc_basename,
                                            source=[ufc_basename+".i"])
        ufc_so = swig_env.SharedLibrary(target=ufc_basename, source=ufc_wrap)[0]
        
        # A SCons bug workaround. Fixed in newer SCons versions
        ufc_py = File(join(dirname(ufc_basename),basename(str(ufc_py))))

        # Set up installation targets
        env.Install(join(env["includeDir"], "swig"),File(ufc_basename+".i"))
        env.Install(env["pythonExtDir"],[ufc_py,ufc_so])
        targets.append(env["pythonExtDir"])

# Set the alias for install
env.Alias("install", targets)

# Create installation target folders if they don't exists:
if 'install' in COMMAND_LINE_TARGETS:
    for target_dir in [env.subst(d) for d in targets]:
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

# If the user are cleaning remove any old ufc python modules
#if env.GetOption("clean") and isdir(join(env.subst(env["pythonModuleDir"]),"ufc")):
if old_ufc_modules and env["cleanOldUFC"]:
    Clean(env["pythonModuleDir"],old_ufc_modules)

if not env.GetOption("clean"):
    import atexit
    if 'install' not in COMMAND_LINE_TARGETS:
        end_message += """
---------------------------------------------------------
Compilation of UFC finished. Now run

    scons install

to install UFC on your system. Note that you may need
to be root in order to install. To specify an alternative
installation directory, run

    scons install prefix=<path>

---------------------------------------------------------
"""
    def out():
        from SCons.Script import GetBuildFailures
        build_failures = GetBuildFailures()
        if build_failures:
            for bf in build_failures:
                print "%s failed: %s" % (bf.node, bf.errstr)
            return
        if not env.GetOption('clean') and not env.GetOption('help'):
            print end_message
    atexit.register(out)

