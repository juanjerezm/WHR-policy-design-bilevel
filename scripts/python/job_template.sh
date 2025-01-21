
    #!/bin/sh
    
    #BSUB -J ${project}_${scenario}
    #BSUB -q man

    #BSUB -n 8
    #BSUB -R "span[hosts=1]"
    #BSUB -R "rusage[mem=8GB]"
    #BSUB -M 8GB
    #BSUB -W 12:00 

    #BSUB -B 
    #BSUB -N 

    #BSUB -oo results/${project}/${scenario}/Output_%J.out 
    #BSUB -eo results/${project}/${scenario}/Error_%J.err 
    
    ### Get paths to GAMS 37
    export PATH=/appl/gams/37.1.0:$PATH
    # export LD_LIBRARY_PATH=/appl/gams/37.1.0:$LD_LIBRARY_PATH

    gams scripts/gams/policy --project=${project} --scenario=${scenario} --timeseries=${timeseries} --tax_carbon=${tax_carbon} --subsidy_capex=${subsidy_capex} --subsidy_opex=${subsidy_opex} --subsidy_carbon=${subsidy_carbon} o=results/${project}/${scenario}/policy.lst
    
