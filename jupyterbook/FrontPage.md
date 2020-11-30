# Introduction to Tawnycalc

*Status badges go here (githubb actions)*

`tawnycalc` provides tools for the orchestration of `thermocalc` simulations
from a Python environment.

This package operates as a high level wrapper to `thermocalc`, allowing 
users to configure, execute and analyse their models.Generally models will
be configured in one of two ways:

  1. Utilise existing `thermocalc` setup scripts. In this case `tawnycalc` 
    will read in the existing input files and present them as Python objects
    for further modification. This is useful for where you have an existing 
    model that you would like to control from Python.
  2. Start from scratch. Here the user will generate the entire configuration
    required for `thermocalc` from within Python. This workflow consolidates 
    your entire model configuration to the Python environment which may 
    provide a more streamlined experience. 

Once configured satisfactorily, execution is performed as follows:

  1. `tawnycalc` utilises the current `Context` configuration to generate
    `thermocalc` input files. These files are generated in either a temporary
    or user specified location
  2. A sub-process is spawned which executes `thermocalc` against the generated
    input files. 

The results of the `thermocalc` execution are then parsed by `tawnycalc` and 
provided as Python objects for analysis. The user may use the results to 
determine the input configuration for further `thermocalc` executions.

Note that this package does not provide the required `thermocalc` executable 
itself. Refer to the `tawnycalc.Context` class for further information. 
## Links

  - [Tawnycalc on Github](https://github.com/underworldcode/tawnycalc)
  <!-- - [API documentation](https://underworldcode.github.io/quagmire/0.9.5_api) -->
