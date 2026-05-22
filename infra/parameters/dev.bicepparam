using '../main.bicep'

param baseName = 'docproc'
param env = 'dev'
param region = 'weu'
param location = 'westeurope'
param enableFreeTier = true
param existingCae = false
param caLocation = 'northeurope' // westeurope AKS capacity exhausted; CAE deployed to northeurope
