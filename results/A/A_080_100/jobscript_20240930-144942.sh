
    #!/bin/sh
    
    #BSUB -J A_A_080_100
    #BSUB -q man

    #BSUB -n 8
    #BSUB -R "span[hosts=1]"
    #BSUB -R "rusage[mem=16GB]"
    #BSUB -M 16GB
    #BSUB -W 06:00 

    #BSUB -B 
    #BSUB -N 

    #BSUB -oo results/A/A_080_100/Output_%J.out 
    #BSUB -eo results/A/A_080_100/Error_%J.err 
    
    ### Get paths to GAMS 37
    export PATH=/appl/gams/37.1.0:$PATH
    export LD_LIBRARY_PATH=/appl/gams/37.1.0:$LD_LIBRARY_PATH

    gams scripts/gams/policy --project=A --scenario=A_080_100 --timeseries=spacing_120 --tax_carbon=no --subsidy_capex=no --subsidy_opex=yes --subsidy_carbon=no o=results/A/A_080_100/policy.lst
    
