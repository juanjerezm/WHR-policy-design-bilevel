
    #!/bin/sh
    
    #BSUB -J E_E_095_100
    #BSUB -q man

    #BSUB -n 8
    #BSUB -R "span[hosts=1]"
    #BSUB -R "rusage[mem=16GB]"
    #BSUB -M 16GB
    #BSUB -W 06:00 

    #BSUB -B 
    #BSUB -N 

    #BSUB -oo results/E/E_095_100/Output_%J.out 
    #BSUB -eo results/E/E_095_100/Error_%J.err 
    
    ### Get paths to GAMS 37
    export PATH=/appl/gams/37.1.0:$PATH
    export LD_LIBRARY_PATH=/appl/gams/37.1.0:$LD_LIBRARY_PATH

    gams scripts/gams/policy --project=E --scenario=E_095_100 --timeseries=spacing_120 --tax_carbon=yes --subsidy_capex=no --subsidy_opex=no --subsidy_carbon=no o=results/E/E_095_100/policy.lst
    
