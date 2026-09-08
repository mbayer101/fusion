#!/bin/bash
#SBATCH --job-name=fusion_neutronics_prod
#SBATCH --output=openmc_%j.out
#SBATCH --error=openmc_%j.err
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=32
#SBATCH --time=08:00:00
#SBATCH --partition=compute

# Load necessary environment modules (adjust to your cluster setup)
module load openmpi/4.1.x
source /root/miniforge3/bin/activate openmc_dagmc_env

echo "======================================================="
echo "Starting Distributed OpenMC Fusion Run"
echo "Job ID: $SLURM_JOB_ID"
echo "Assigned Nodes: $SLURM_JOB_NODELIST"
echo "Total MPI Ranks: $SLURM_NTASKS"
echo "======================================================="

# Execute OpenMC using MPI across allocated nodes
mpirun -np $SLURM_NTASKS openmc --mpi

echo "======================================================="
echo "Simulation completed successfully at $(date)"
echo "======================================================="
