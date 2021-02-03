# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
from .data_objects import xyz, site_fractions, thermodynamic_properties, rbi, Printable_OrderedDict, thermocalc_script, Results

class Context(object):
    """
    The class records a context for a `thermocalc` computation.
    Multiple concurrent running contexts are allowed.

    The default behaviour is for the context to leverage the standard 
    `thermocalc` input files to for model setup. The user may optionally
    also start with an empty context and construct their model from the 
    ground up.

    The `thermocalc` executable must be available somewhere on the user 
    system. To use the executable, the the script will consider, in order 
    of preference:

    1. User provided `tc_executable` parameter to this class.
    2. User set environment variable `THERMOCALC_EXECUTABLE` defining
       the absolute path to the executable. 
    3. Run directly, with executable therefore available in current
       directory or available via the system `PATH`. 

    Note that the execution is performed in a temporary location such
    that all files in the current context location are not modified or
    written over. This location may be specified as a parameter. 

    Params
    ------
    scripts_dir: str
        Path to find thermocalc files (in particular `tc-prefs.txt`).
        Defaults to current directory, which is usually the directory where
        Python was launched from. Set to `None` to obtain an empty context. 
    tc_executable: str
        Thermocalc executable. Check class descriptor for further information.
    temp_dir: str
        Temporary location used for the `thermocalc` execution. If not specified,
        a standard system location is used. 
    """
    def __init__(self, scripts_dir=os.getcwd(), tc_executable=None, temp_dir=None):
        # lets first check that we have an executable
        # the following is borrowed from https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
        def which(program):
            def is_exe(fpath):
                return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

            fpath, fname = os.path.split(program)
            if fpath:
                if is_exe(program):
                    return program
            else:
                for path in os.environ["PATH"].split(os.pathsep):
                    exe_file = os.path.join(path, program)
                    if is_exe(exe_file):
                        return exe_file
            return None

        if tc_executable:
            # Test explicitly specified executable
            self.exec = which(tc_executable)
            if self.exec is None:
                raise RuntimeError("Parameter specified executable {} does not appear to be valid".format(tc_executable))
        elif "THERMOCALC_EXECUTABLE" in os.environ:
            # Test environment variable specified executable
            self.exec = which(os.environ["THERMOCALC_EXECUTABLE"])
            if self.exec is None:
                raise RuntimeError("Environment specified executable {} does not appear to be valid".format(os.environ["THERMOCALC_EXECUTABLE"]))
        else:
            # Test distributed executable
            package_dir = os.path.dirname(os.path.realpath(__file__))
            bin_dir = os.path.join(package_dir,"bin")
            import platform
            self.exec = which(os.path.join(bin_dir,"thermo_"+platform.system()))
            # Test for executable in PATH
            if not self.exec:
                self.exec = which('thermo')
                if self.exec is None:
                    raise RuntimeError("Unable to find `thermo` executable. Ensure it is in your path, or set " \
                                    "the `THERMOCALC_EXECUTABLE` environment variable, or the `tc_executable` parameter.")
        self.scripts_dir = scripts_dir
        def randomword():
            import random, string
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(6))
        self._id = randomword()
        self.reload()


        if not temp_dir:
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), 'TC_'+self._id)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.temp_dir = temp_dir

    def reload(self):
        """
        Reloads data from working directory.
        """
        # create some defaults
        self._prefs = thermocalc_script()
        self._prefs["setpagewidth"] = 255
        self._prefs["calcmode"] = 1
        self._prefs["scriptfile"] = self._id
        self._prefs["dataset"] = None
        # create an ordered dictionary to record key/value pairs
        self._script = thermocalc_script()
        self._script["axfile"] = None
        self._script["autoexit"] = ""

        # load from existing inputs if required
        if self.scripts_dir:
            # find tc-prefs.txt        
            tc_prefs = os.path.join(self.scripts_dir,'tc-prefs.txt')
            # read tc-prefs
            self._prefs.load(tc_prefs)
            if 'scriptfile' not in self.prefs:
                raise RuntimeError("'scriptfile' does not appear to be specified in 'tc-prefs.txt' file.")

            # find dataset 
            ds = 'tc-ds' + self.prefs['dataset'] + '.txt'
            tc_ds = os.path.join(self.scripts_dir,ds)
            if not os.path.isfile(tc_ds):
                raise RuntimeError("Unable to find dataset file '{}' in '{}'".format(ds,self.scripts_dir))

            # find scriptfile 
            sf = 'tc-' + self.prefs['scriptfile'] + '.txt'
            tc_sf = os.path.join(self.scripts_dir,sf)
            self._script.load(tc_sf)
            self.check_config()


    def check_config(self):
        """
        This method performs sanity checks on your current configuration. 

        It will return nothing if it does not detect any issues, and will 
        raise an exception otherwise.  
        """
        if 'dataset' not in self.prefs:
            raise RuntimeError("'dataset' does not appear to be specified in 'tc-prefs.txt' file.")
        if 'calcmode' not in self.prefs:
            raise RuntimeError("'calcmode' does not appear to be specified in 'tc-prefs.txt' file.")
        if int(self.prefs['calcmode']) != 1:
            raise RuntimeError("Python wrappers currently only support 'calcmode' 1.")

        if "axfile" not in self._script:
            raise RuntimeError("Your script must specify an 'axfile'.")
        if self._script["axfile"] == None:
            raise RuntimeError("Your script must specify a valid 'axfile'.")

    @property
    def prefs(self):
        """
        The `prefs` dictionary contains your `thermocalc` preferences. 
        This dictionary will be populated with the data from your `scripts_dir` 
        directory, if this parameter is set. Otherwise it will be empty and 
        you will be required to sufficiently populate it. In either case, 
        you may add, modify and delete values as necessary before calling `execute`. 

        Please see `help(tawnycalc.data_objects.thermocalc_script)` for further
        info on object usage.
        """
        return self._prefs

    @property
    def script(self):
        """
        The `script` dictionary contains your `thermocalc` model configuration. 
        This dictionary will be populated with the data from your `thermocalc` 
        scripts where the `scripts_dir` parameter is passed when constructing
        your `Context`.  Otherwise it will be empty and you will be required 
        to sufficiently populate it.  In either case, you may add, modify and
        delete values as necessary before calling `execute`. 

        Please see `help(tawnycalc.data_objects.thermocalc_script)` for further
        info on script object usage.
        """
        return self._script

    def execute(self, timeout=10, copy_new_files=False, datasets_dir=None):
        """
        Execute thermocalc for the current configuration, and parse generated
        outputs. Recorded outputs include execution standard output (`stdout`),
        standard error (`stderr`), `tc-log.txt` and `tc-ic.txt`.

        Files generated as a result of the execution are as default not copied
        back to the context location.

        All results are returned as a dictionary. Refer to the list of dictionary 
        keys to get a list of returned data:

        >>> results = mycontext.execute()
        >>> results.print_keys()
        P
        T
        bulk_composition
        modes
        output_tc_ic
        phases
        rbi
        site_fractions
        thermodynamic_properties
        xyz

        Note that dictionary entries can be accessed directly as attributes or via 
        the usual dictionary methods:

        >>> results.P
        11.0
        >>> results["P"]
        11.0


        Params
        ------
        timeout: int
            How long to wait for THERMOCALC calculation to complete.
        copy_new_files: bool
            Files which are generated resultant of the `thermocalc` execution are by 
            default not copied back to the context location. Enable this flag to have
            generated files copied. 
        datasets_dir: string
            Location of required datasets. It is usually not necessary to specify this
            as the files will be obtained from the `scripts_dir` or from `tawnycalc` 
            itself. 

        Returns
        -------
        results: dict
            Dictionary containing execution results.
        """
        self.check_config()

        if copy_new_files:
            import warnings
            warnings.warn("'copy_new_files' not yet implemented.\nGenerated files may be found in {}".format(self.temp_dir))

        # write prefs file to temp location
        self.prefs.save(os.path.join(self.temp_dir,"tc-prefs.txt"))

        # write script file
        self.script.save(os.path.join(self.temp_dir,"tc-"+self.prefs['scriptfile']+".txt"))

        # if not provided in this call
        if not datasets_dir:
            # set to scripts dir provided when context created.
            datasets_dir = self.scripts_dir
        # if still nothing
        if not datasets_dir:
            # use python module files
            datasets_dir = os.path.join(__file__[:-7],"datasets")
        
        # now copy dataset file
        from shutil import copyfile
        dataset = "tc-ds{}.txt".format(self.prefs['dataset'])
        copyfile(os.path.join(datasets_dir,dataset), os.path.join(self.temp_dir,dataset))

        # now copy axfile
        axfile = "tc-{}.txt".format(self._script['axfile'])
        copyfile(os.path.join(datasets_dir,axfile), os.path.join(self.temp_dir,axfile))

        outfile = "tc-{}.txt".format("tawnyout")
        writer = open(os.path.join(self.temp_dir,outfile),'w',encoding="cp437")
        from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
        p = Popen(self.exec,cwd=self.temp_dir, stdout=writer, stdin=PIPE, stderr=STDOUT)
        # if print_output:
            # for line in iter(p.stdout.readline, b''):
            #     print('{}'.format(line.decode("cp437").rstrip()))
        try:
            std_data = p.communicate(input=b'n\n', timeout=timeout)
        except TimeoutExpired as e:
            msg =   "\nTHERMOCALC did not complete execution within the timeout limit.\n\n"\
                    "If your model specification was incomplete, THERMOCALC may have\n"\
                    "been waiting for interactive user input. Alternatively, execution\n"\
                    "may simply have required further time.\n\n"\
                    "You may set a custom timeout using the `timeout` parameter:\n"\
                    "`context.execute(timeout=...)`\n\n"\
                    "To view the output generated by THERMOCALC for this execution,\n"\
                    "call the `print_output()` method:\n"\
                    "`context.print_output()`\n\n"\
                    "If you would instead like to run THERMOCALC directly, all the \n"\
                    "necessary files are located in:\n" + str(self.temp_dir)
            raise RuntimeError(msg)
        finally:
            p.terminate()
            writer.close()
        writer.close()

        results = Results()

        # try parse `tc-log.txt`
        try:
            with open(os.path.join(self.temp_dir,"tc-log.txt"),'r',encoding="cp437") as fp:
                while True:
                    line = fp.readline()
                    if not line: break
                    splitline = line.split()
                    if len(splitline)>0:
                        key = splitline[0]
                        value = splitline[1:]
                        if   key=="THERMOCALC":
                            # let's check version
                            try:
                                # grab first line
                                version = splitline[1]
                                if version != "3.50":
                                    import warnings
                                    warnings.warn("`tawnycalc` only tested against `thermocalc` version 3.50. Detected version is {}.".format(version))
                            except:
                                import warnings
                                warnings.warn("Unable to detect `thermocalc` version. Note that `tawnycalc` only tested against `thermocalc` version 3.50.")
                        elif key=="rbi":
                            if "rbi" not in results.keys():
                                # # grab copy of existing rbi if available and oxides
                                # if ("rbi" in self._script.keys()) and (self._script["rbi"].oxides == value):
                                #     results["rbi"] = self._script["rbi"].copy()
                                # else:
                                results["rbi"] = rbi(value)
                            else:
                                results["rbi"].add_data(value)
                        elif key=="phases:":
                            results["phases"] = " ".join(value)
                        elif key=="ptguess":
                            results["P"] = float(value[0])
                            results["T"] = float(value[1])
                        elif key=="xyzguess":
                            if "xyz" not in results.keys():
                                results["xyz"] = xyz()
                            results["xyz"][value[0]] = float(value[1])
                        elif key=="mode":
                            modes = Printable_OrderedDict()
                            mode_keys   = value                  # keys from first line
                            mode_values = fp.readline().split()  # values from next                            
                            for mode_key,mode_value in zip(mode_keys,mode_values):
                                modes[mode_key] = float(mode_value)
                            results["modes"] = modes

            # try parse `tc-ic.txt`
            filename = "tc-" + self.prefs["scriptfile"] + "-ic.txt"
            with open(os.path.join(self.temp_dir,filename),'r',encoding="cp437") as fp:
                while True:
                    line = fp.readline()
                    if not line: break

                    line = line.strip()
                    if line=="site fractions":
                        site_fracs = site_fractions()
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            site_fracs.add_data(line.split())
                        results["site_fractions"] = site_fracs

                    if line=="oxide compositions":
                        bulk_composition = Printable_OrderedDict()
                        keys = fp.readline().split()    # keys in first line
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            tokens = line.split()
                            if tokens[0] == 'bulk':
                                for key,value in zip(keys,tokens[1:]):
                                    bulk_composition[key] = float(value)
                        results["bulk_composition"] = bulk_composition

                        # now thermo props. 
                        # we assume here that they appear directly after the "oxide composition" section.
                        while True:
                            line = fp.readline()
                            if not line or (line == "\n"): break
                            tokens = line.split()
                            thermo_props = thermodynamic_properties(tokens)
                            while True:
                                line = fp.readline()
                                if not line or (line == "\n"): break
                                thermo_props.add_data(line.split())
                            results["thermodynamic_properties"] = thermo_props
                            break
        except Exception as e:
            raise RuntimeError("An error appears to have been encountered running `THERMOCALC`.\n"\
                               "Check resultant output by running `context.print_output()`.") from e
        # ok, grab entire output for user's convenience 
        with open(os.path.join(self.temp_dir,filename),'r',encoding="cp437") as fp:
            results["output_tc_ic"] = fp.read()

        return results

    def print_output(self, num_lines=100, max_line_length=120):
        """
        Prints the output generated during the previous THERMOCALC execution.

        Params
        ------
        num_lines: int
            Number of lines to print.
        max_line_length: int
            Number of characters to be printed from each line.
        """

        outfile = "tc-{}.txt".format("tawnyout")
        with open(os.path.join(self.temp_dir,outfile),'r',encoding="cp437") as f:
            line_count = 0
            while line_count<num_lines:
                line = f.readline(max_line_length)
                if line=="":
                    break 
                print(line[:-1])
                line_count+=1
