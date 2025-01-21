
    #!/bin/sh
    
    #BSUB -J B_B_090_120
    #BSUB -q man

    #BSUB -n 8
    #BSUB -R "span[hosts=1]"
    #BSUB -R "rusage[mem=16GB]"
    #BSUB -M 16GB
    #BSUB -W 06:00 

    #BSUB -B 
    #BSUB -N 

    #BSUB -oo results/B/B_090_120/Output_%J.out 
    #BSUB -eo results/B/B_090_120/Error_%J.err 
    
    ### Get paths to GAMS 37
    export PATH=/appl/gams/37.1.0:$PATH
    export LD_LIBRARY_PATH=/appl/gams/37.1.0:$LD_LIBRARY_PATH

    gams scripts/gams/policy --project=B --scenario=B_090_120 --timeseries=spacing_120 --tax_carbon=no --subsidy_capex=yes --subsidy_opex=no --subsidy_carbon=no o=results/B/B_090_120/policy.lst
    
