import os, warnings


def wt2mol(oxides, comp_in_wt):
    """
    Converts a composition in mass-based proportions of oxides
    (`wt%', need not be normalised) 
    to a composition in mole % oxides.
    """
    if isinstance(oxides,str):
        oxlist = oxides.split()
    else:
        oxlist = oxides
    if isinstance(comp_in_wt,str):
        oxide_complist = [ float(i) for i in comp_in_wt.split() ]
    else:
        oxide_complist = comp_in_wt
    ox_mass_per_mol = [ oxide_data().molar_masses[l] for l in oxlist ]
    ox_mol = [ oxide_complist[i]/ox_mass_per_mol[i] for i in range(len(oxlist)) ]
    return [ 100*i/sum(ox_mol) for i in ox_mol ]
    
    
def mol2wt(oxides, comp_in_moles):
    """
    Converts a composition in mole percent oxides
    to a composition in `wt%' (i.e. mass-based proportions) of oxides.
    """
    if isinstance(oxides,str):
        oxlist = oxides.split()
    else:
        oxlist = oxides
    if isinstance(comp_in_moles,str):
        oxide_complist = [ float(i) for i in comp_in_moles.split() ]
    else:
        oxide_complist = comp_in_moles
    ox_mass_per_mol = [ oxide_data().molar_masses[l] for l in oxlist ]
    ox_mass = [ oxide_complist[i]*ox_mass_per_mol[i] for i in range(len(oxlist)) ]
    return [ 100*i/sum(ox_mass) for i in ox_mass ]    


def atoms_from_oxides(oxides, oxide_comp):
    """
    Calculates the total number of atoms, given a composition as
    a vector of numbers of oxide units, and dictionary of numbers 
    of atoms per oxide.
    The oxides must be named in the same order as they appear
    in the compositional vector.
    """        
    if isinstance(oxides,str):
        oxlist = oxides.split()
    else:
        oxlist = oxides
    if isinstance(oxide_comp,str):
        oxide_complist = [ float(i) for i in oxide_comp.split() ]
    else:
        oxide_complist = oxide_comp         
    nAox_dict = oxide_data().atoms_per_oxide
    nAox = [ nAox_dict[i] for i in oxlist ]
    return sum([ x * y for x, y in zip(oxide_complist,nAox) ])


class oxide_data:
    """
    A class that reads in and processes ./datasets/oxide_data.txt, providing:
     oxide_data().tcalc_oxides:      
                        list of oxides recognised by THERMOCALC, in canonical order
     oxide_data().atoms_per_oxide:
                        dictionary of number of atoms in each oxide
     oxide_data().molar_masses:  
                        dictionary of molecular mass for each oxide, as used by THERMOCALC 
    """        
    def __init__(self):
        self.datasets_dir = os.path.join(__file__[:-18],"datasets")
        self.datafile = self.datasets_dir+"/oxide_data.txt"
        try:
            with open(self.datafile) as lst:
                oxdat0=lst.readlines()    
            self.oxdat = [ l.split() for l in oxdat0 ]
            lAox = [ l for l in self.oxdat if (len(l)>0 and l[0]=='no_atoms') ][0][1:]
            self.nAox = [ int(a) for a in lAox]
            lWox = [ l for l in self.oxdat if (len(l)>0 and l[0]=='molar_wt') ][0][1:]
            self.nAox = [ int(a) for a in lAox]
            self.mWox = [ float(a) for a in lWox]     
            self.tcalc_oxides = [ l for l in self.oxdat if (len(l)>0 and l[0]=='oxides') ][0][1:]
            self.atoms_per_oxide = { self.tcalc_oxides[i] : self.nAox[i] for i in range(len(self.tcalc_oxides)) }
            self.molar_masses = { self.tcalc_oxides[i] : self.mWox[i] for i in range(len(self.tcalc_oxides)) }        
        except Exception as exc:
            raise RuntimeError("Unable to parse `oxide_data.txt', expected in\n {}".format(self.datasets_dir)) from exc
    

class deconstruct_rbi:
    """
    Decomposes an rbi block to extract: 
    - lists of oxides, phases and modes
    - a list of lists of phase compositions.
    If normalise_modes=True (default), it ensures that the modes of phases 
    sum to 1 (always true for THERMOCALC output; not necessarily for user input).
    """
    def __init__(self,rbi_block,normalise_modes=True):
        self.rbi_block = rbi_block        
        self.phases = list(self.rbi_block.keys())  # all phases in rbi object
        key1 = list(self.rbi_block.keys())[0]
        self.oxides = list(self.rbi_block[key1].keys())[1:]
        modes0 = [ float(self.rbi_block[phase]["mode"]) for phase in self.phases ]
        if normalise_modes:
            self.modes = [ m/sum(modes0) for m in modes0 ]
        else:
            self.modes = modes0
        self.phase_comps = [ [ float(self.rbi_block[ph][ox]) for ox in self.oxides ] for ph in self.phases ]
                    

    
class bulk_composition:
    """
    Calculates the number of oxide units and total number of 
    atoms in a specified subset of the phases in an rbi construct.
       
    Params
    ------
    rbi_block:    an rbi construct
    phases:       list of names of phases from the rbi construct 
                     as strings; OR, "all" for whole rbi block (default)
    phase_fractions:
                  list of multipliers on the modes of phases in
                  the subset, allowing for partial addition/removal
                  of phases. By default, treated as [1,1,...].
    """
    
    def __init__(self, rbi_block, phases="all", phase_fractions=[]):
        self.rbi_block = rbi_block
        self.phases = phases
        self.phase_fractions = phase_fractions         
  
        # ensure modes in entire rbi block are normalised
        # (true for THERMOCALC output but not necessarily for user input)
        rbi_obj = deconstruct_rbi(rbi_block,normalise_modes=True)
        phases0 =  rbi_obj.phases
        oxides = rbi_obj.oxides    
        modes0N = rbi_obj.modes
        
        # for each phase in the specified subset, find the numbers of
        # oxide units contributed to the system
        oxlists = []   
        modes = []
        if phases == 'all':
            phase_subset = phases0
        else:
            phase_subset = phases
        if phase_fractions == []:
            phfr = dict(zip(phase_subset, [ 1 for i in range(len(phase_subset))] ))
        else:
            phfr = 1
            phfr = dict(zip( phase_subset, phase_fractions  ))    
        
        for phase in phase_subset:
            pos = phases0.index(phase)
            mode = modes0N[pos]*phfr[phase]   # no. atoms of phase = mode
            modes.append(mode)
            oxx = [ float(self.rbi_block[phase][x]) for x in oxides ]
            apfu = atoms_from_oxides(oxides,oxx)      # atoms per formula unit
            oxf = [ mode * x / apfu for x in oxx ] 
            oxlists.append(oxf)
    
        # for each oxide, sum the contributions from each of the phases
        # in the specified subset, and calculate the total number of atoms
        oxlistsT = [ [oxlists[j][i] for j in range(len(oxlists))] for i in range(len(oxlists[0])) ]
        oxide_sums = [ sum(l) for l in oxlistsT ]
        oxide_percent = [ 100*i/sum(oxide_sums) for i in oxide_sums ]
        self.numbers_of_oxides = dict(zip(oxides, oxide_sums))
        self.molepc_oxides = dict(zip(oxides, oxide_percent))
        self.sum_of_modes = sum(modes)


class partial_property:
    """
    For an extensive property of the system (e.g. volume, energy, mass), this 
    class constructs the contribution by each phase (the "partial" values of the
    property) to the value for the whole system (the "bulk" property).
    
    It requires the value of the extensive property as specified for each phase 
    on a per-formula-unit (p.f.u.) basis. It converts the p.f.u. values to a
    per-atom basis, and weights by the modes of phases present in the system.  

    Args
    ------
    rbi_block               An rbi block defining the system.
    partial_property_pfu    A list of values (floats) of an extensive property for each 
                            phase, on a per-formula-unit (p.f.u.) basis, e.g. 
                            [volume_pfu_phase1, volume_pfu_phase2, ...], where the order
                            of the phases must match the order in the rbi block. 
    f  (default=[])         List of per-formula-unit to per-atom conversion factors for 
                            each phase. THERMOCALC's calculated values may be passed to 
                            the function to reduce rounding error; otherwise f will be 
                            calculated internally.                                            
    """
    
    def __init__(self, rbi_block, partial_property_pfu, f=[]):
        self.rbi_block = rbi_block
        self.partial_property_pfu = partial_property_pfu
        self.f = f              
        if (len(partial_property_pfu)>0 and isinstance(partial_property_pfu[0], float)):      
            rbi_obj = deconstruct_rbi(rbi_block,normalise_modes=False)
            phases =  rbi_obj.phases
            oxides = rbi_obj.oxides    
            modes = rbi_obj.modes 
            phindex = range(len(phases))
            phase_comps_pfu = rbi_obj.phase_comps 
            bulk_comp0 = bulk_composition(self.rbi_block).numbers_of_oxides
            bulk_comp = [ bulk_comp0[ox] for ox in oxides ]
            bulk_atoms = atoms_from_oxides(oxides, bulk_comp)
            if f == []:
                atoms_pfu = [ atoms_from_oxides(oxides, phase_comp) for phase_comp in phase_comps_pfu ]
                ff = [ bulk_atoms/(100*atoms_pfu[i]) for i in phindex ]
            else: 
                ff = f    
            self.values = [ partial_property_pfu[i] * modes[i] * ff[i] for i in phindex ] 
        else:
            warnings.warn("Class `partial_property` takes property values as list of floats")                    