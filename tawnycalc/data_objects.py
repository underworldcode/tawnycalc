from collections import OrderedDict
from .chemical_system import oxide_data
import warnings

class Printable_OrderedDict(OrderedDict):
    """
    This class simply redefines `__repr__` method so that
    objects can be printed nicely. 
    """
    def __repr__(self):
        """
        This should a user friend representation.
        """
        from tabulate import tabulate
        return tabulate(self.items(),tablefmt="plain")
    
class xyz(OrderedDict):
    """
    Container for mineral composition data. 
    """
    pass

class site_fractions(OrderedDict):
    """
    Container to hold site fraction info.

    """
    def __init__(self):
        self._data_title=None
        pass

    def add_data(self, line):
        """
        Adds data from a provided tokenised line of data. 

        We expect data formatted like the following:

            g          xMgX      xFeX      xCaX      xAlY     xFe3Y
                    0.13698   0.82757   0.03545   0.98451   0.01549
            bi        xMgM3     xFeM3    xFe3M3     xTiM3     xAlM3    xMgM12    xFeM12      xSiT      xAlT      xOHV       xOV
                    0.23132   0.50716   0.05416   0.09110   0.11627   0.47293   0.52707   0.41479   0.58521   0.90890   0.09110
            mu          xKA      xNaA      xCaA    xMgM2A    xFeM2A    xAlM2A    xAlM2B   xFe3M2B     xSiT1     xAlT1
                    0.76707   0.22980   0.00313   0.05172   0.04523   0.90305   0.99381   0.00619   0.54691   0.45309
            pa          xKA      xNaA      xCaA    xMgM2A    xFeM2A    xAlM2A    xAlM2B   xFe3M2B     xSiT1     xAlT1
                    0.06836   0.91840   0.01324   0.00170   0.00149   0.99681   0.99881   0.00119   0.49498   0.50502

        This method should be provided with the above data, one split line per call. The order 
        the provided lines must follow the order of the data to ensure correct parsing. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """

        splitline = line
        if self._data_title == None:
            self._data_title = splitline[0]
            # grab first token for dictionary key
            currentdict = self[self._data_title] = OrderedDict()
            # populate keys for sub-dictionary
            for token in splitline[1:]:
                currentdict[token] = None
        else:
            currentdict = self[self._data_title]
            for key,value in zip(currentdict.keys(),splitline):
                currentdict[key] = value
            self._data_title = None
    
    def _generate_table_rows(self):
        rows = []
        for key,item in self.items():
            row = [key,] + list(item.keys())
            rows.append(row)
            rows.append(["",]+list(item.values()))
        return rows

    def __repr__(self):
        """
        This should print a user friendly representation.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
    
    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        rows = self._generate_table_rows()
        from tabulate import tabulate
        return tabulate(rows,tablefmt="plain")

class _tabled_data(OrderedDict):
    """
    Container class to hold data derived of table layout.

    Params
    ------
    header: list
        The table header info.

    """
    def __init__(self, header):
        self.header = []
        for item in header:
            self.header.append(item.strip())

    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        raise RuntimeError("Child must define.")
    
    def _generate_table_rows(self):
        rows = [ ["",]+self.header, ]
        for key,item in self.items():
            row = [key,] + list(item.values())
            rows.append(row)
        return rows

    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
 
    def __repr__(self):
        """
        This should print a user friendly representation.
        """
        return self.__str__()

    def __copy__(self):
        cls = self.__class__
        copyobj = cls.__new__(cls)
        copyobj.__dict__.update(self.__dict__)
        return copyobj

    def __deepcopy__(self, memo):
        from copy import deepcopy
        cls = self.__class__
        copyobj = cls.__new__(cls)
        memo[id(self)] = copyobj
        # copy attribs
        for k, v in self.__dict__.items():
            setattr(copyobj, k, deepcopy(v, memo))
        # copy dict content
        for k, v in self.items():
            print(k)
            copyobj[k] = deepcopy(v, memo)
        return copyobj

    def copy(self):
        """
        Returns a deep copy of the current object.
        """
        import copy
        return copy.deepcopy(self)

class thermodynamic_properties(_tabled_data):
    """
    Container class for thermodynamic properties parsed
    from tc-ic file. 
    """
    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        if (line[0] == 'sys' or line[0] == 'bulk'):
            if 'mode' in self.header:
                line.insert( self.header.index('mode')+1, '-')
            if 'f' in self.header:
                line.insert( self.header.index('f')+1, '-') 
        if len(line) != len(self.header)+1:
            raise RuntimeError("Error parsing thermodynamic data.\nExpected property count ({}) is different from that encountered ({}) for phase '{}'.".format(len(self.header),len(line)-1,line[0]))
        phase_dict = self[line[0]] = OrderedDict()
        for key,value in zip(self.header,line[1:]):
            phase_dict[key] = value

class rbi(_tabled_data):
    """
    Simple container class to hold rbi information.

    Params
    ------
    oxides: list
        list of oxides. Ie, the rbi columns.
        List must be a subset of the oxides recognised by THERMOCALC, and 
        conform with the expected order. The THERMOCALC oxides can be obtained
        from 'oxide_data().tcalc_oxides'. 

    """
    def __init__(self, oxides):
        if isinstance(oxides, str):
            oxides = oxides.split()
        super().__init__(header=oxides)
        self.oxides = self.header
        oxide_order = oxide_data().tcalc_oxides
        self.invalid_oxides = [ i for i in self.oxides if i not in oxide_order]
        if self.invalid_oxides:
            invalid_oxide_str = ", ".join(self.invalid_oxides)
            warnings.warn("The following oxides cannot be handled and must be removed: {}".format(invalid_oxide_str))
        else:
            self.ordered_oxides = [ i for i in oxide_order if i in self.oxides]
            if self.oxides != self.ordered_oxides:   
                ordered_oxide_str =  ", ".join(self.ordered_oxides)      
                warnings.warn("Incorrect oxide order: must be {}".format(ordered_oxide_str))
        

    def add_data(self, line):
        """
        Adds data from a provided parsed line of data. 

        Params
        ------
        line:  list
            List of string tokens read from the a TC input/output.
        """
        self.add_phase(phase=line[0],mode=line[1],oxides=line[2:])

    def add_phase(self, phase, mode, oxides):
        """
        Add a phase to the rbi table. 

        Params
        ------
        phase:  str
            Name of phase to add. 
        mode: str, float
            Mode/proportion of phase.
        oxides: str,list
            Proportion of each oxide for phase. 
        """
        # create a dictionary for phase. 
        phase = phase.strip()
        self[phase] = OrderedDict()
        self[phase]["mode"] = float(mode)
        if isinstance(oxides, str):
            oxides = oxides.split()
        if len(self.oxides) != len(oxides):
            raise RuntimeError("Error parsing 'rbi' data.\nExpected oxide count ({}) is different from that encountered ({}) for phase '{}'.".format(len(self.oxides),len(oxides),phase))
        for item in zip(self.oxides,oxides):
            self[phase][item[0]]=float(item[1])
    
    def _generate_table_rows(self):
        rows = [ ["",""]+self.oxides, ]
        for key,item in self.items():
            row = [key,] + list(item.values())
            rows.append(row)
        return rows

    def __repr__(self):
        """
        This should print a user friendly representation.
        """
        from tabulate import tabulate
        return tabulate(self._generate_table_rows(),tablefmt="plain")
    
    def __str__(self):
        """
        This should generate a TC compatible string.
        """
        rows = self._generate_table_rows()
        for row in rows:
            row.insert(0, "rbi")
        from tabulate import tabulate
        return tabulate(rows,tablefmt="plain")

    def copy(self):
        """
        Returns a copy of current rbi object
        """
        cpy = rbi(self.oxides)        
        for key,val in self.items():
            cpy[key]=val.copy()
        return cpy

class thermocalc_script(OrderedDict):
    """
    This dictionary class generates objects which represent `thermocalc` scripts 
    and provides associated methods to handle the script lifecycle and user 
    interaction.

    Key/Value pairs will be directly printed to form standard `thermocalc`
    input.  For example 

    >>> context.script[       "axfile"] = "mb50NCKFMASHTO"
    >>> context.script[        "which"] = "chl bi pa ep ru chl g ilm sph"
    >>> context.script[     "inexcess"] = "mu q H2O"
    >>> context.script[       "dogmin"] = "yes 0"

    is equivalent to

        axfile   mb50NCKFMASHTO
        which    chl bi pa ep ru chl g ilm sph
        inexcess mu q H2O
        dogmin   yes 0

    To form repeat keyword entries, set the required corresponding values 
    in a Python list.  For example:

    >>> context.script[   "samecoding"] = ["mu pa", "sp mt"]

    is equivalent to

        samecoding mu pa
        samecoding sp mt

    Params
    ------
    filename: str
        Optional. If provided, script is loaded from specified file.

    """
    def __init__(self, filename=None):
        super(thermocalc_script, self).__init__()
        if filename:
            self.load(filename)

    def load(self, filename):
        """
        Load `thermocalc` script file from disk.

        Params
        ------
        filename: str
            Name of script file to be loaded, including full or 
            relative path.
        """
        import os
        if not os.path.isfile(filename):
            raise RuntimeError("Unable to find scriptfile '{}'".format(filename))

        # read script file
        # keep track of repeated keys to handle differently
        from collections import defaultdict
        keycount = defaultdict(lambda: 0)
        with open(filename,'r') as fp:
            while True:
                line = fp.readline()
                if not line: break
                # get rid of everything after '%'
                line = line.split("%", 1)[0]
                splitline = line.split()
                if len(splitline)>0:
                    if splitline[0] == '*':                # don't read anything past here
                        break
                    key = splitline[0]
                    value = splitline[1:]
                    # now need to decide how to enter into dictionary.
                    # treat "xyzguess" as dictionary
                    if key=="xyzguess":
                        if "xyzguess" not in self.keys():
                            self["xyzguess"] = xyz()
                        self["xyzguess"][value[0]] = value[1:]
                    elif key=="rbi":
                        if "rbi" not in self:
                            # create `rbi` object and provide `value` for oxide columns
                            self["rbi"] = rbi(value)
                        else:
                            self["rbi"].add_data(value)
                    else:
                        val_count = len(value)
                        if val_count == 0:                   # if no values, just set to None
                            value = None
                        else:
                            value = " ".join(value)
                            if value == 'ask':
                                raise RuntimeError("'ask' keyword in script is not supported from the Python interface.")
                        # first check the number of times this key has been encountered
                        keycount[key]+=1                       # increment key count
                        if   keycount[key] == 1:               # if only encountered once, simply create direct pair
                            self[key] = value
                        if keycount[key] == 2:                 # this is the second time we've encountered this key,
                            rows = list()                      # so create a list store the rows,
                            rows.append(self[key])      # and append previously encountered value as first item in row list.
                            self[key] = rows            # now replace that previous value with the rows list (which contains it). 
                                                                # note that the new value is entered in the following block.
                        if keycount[key] > 1:
                            self[key].append(value)     # append value to rows list of values

    def save(self, filename):
        """
        Save `thermocalc` script to disk.

        Params
        ------
        filename: str
            Name of file for script to be saved to, including full or 
            relative path.
        """
        with open(filename,'w') as fp:
            longest = self._longest_key(self)
            for key, value in self.items():
                if isinstance(value, list):
                    for item in value:
                        fp.write("{} {}\n".format(key,self._get_string(item)))
                elif isinstance(value,rbi):
                    fp.write(str(value)+"\n")
                elif isinstance(value, dict):
                    longest_inner = self._longest_key(value)
                    for valkey,item in value.items():
                        fp.write("{} {} {}\n".format(key,valkey, self._get_string(item,10)))
                else:
                    fp.write("{} {}\n".format(key.ljust(longest+1),self._get_string(value)))

    def __repr__(self):
        """
        Prints the current loaded script configuration.
        """
        longest = self._longest_key(self)
        returnstr = ""
        for key, value in self.items():
            if key=="rbi":
                returnstr += "\n{} :\n".format(key)
                returnstr += repr(value) + "\n\n"
            elif isinstance(value, list):
                returnstr += "{} :\n".format(key)
                for item in value:
                    returnstr += "    {}\n".format(self._get_string(item,10))
            elif isinstance(value, dict):
                returnstr += "{} :\n".format(key)
                longest_inner = self._longest_key(value)
                for valkey,item in value.items():
                    returnstr += "    {} : {}\n".format(valkey.ljust(longest_inner), self._get_string(item,10))
            else:
                returnstr += "{}: {}\n".format(key.ljust(longest+1),self._get_string(value))
        return returnstr

    def copy(self):
        """
        Returns a deep copy of the current script.
        """
        import copy
        return copy.deepcopy(self)

    def _longest_key(self, dictguy):
        """
        Get length of longest dictionary key
        """
        longest = 0
        for key in dictguy:
            if len(key)>longest:
                longest = len(key)
        return longest

    def _get_string(self, item, just=0):
        """
        Prints item or list of items
        """
        if   isinstance(item,list):
            return " ".join(str(p).ljust(just) for p in item)
        return item

class Results(dict):
    """
    A special dictionary which allows keys/vals to be accessed
    via object attributes

    Params
    ------
    filename: str, optional
        Name of file for results to be loaded from, including full or 
        relative path.

    """
    def __init__(self, *args, filename=None, **kwargs):
        super(Results, self).__init__(*args, **kwargs)
        self.__dict__ = self

        if filename:
            self.load(filename)

    def print_keys(self):
        for key in sorted(self.keys()):
            print(key)

    def save(self, filename):
        """
        Save results dictionary to disk in JSON format.

        Params
        ------
        filename: str
            Name of file for results to be saved to, including full or 
            relative path.
        """
        import json
        with open(filename, 'w') as fp:
            json.dump(self, fp)

    def load(self, filename):
        """
        Load results dictionary from disk.

        Params
        ------
        filename: str
            Name of file for results to be loaded from, including full or 
            relative path.
        """
        import json
        with open(filename, 'r') as fp:
            self.update(json.load(fp))

    def copy(self):
        """
        Returns a deep copy of the current object.
        """
        import copy
        return copy.deepcopy(self)

