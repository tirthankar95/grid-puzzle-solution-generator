#!/bin/bash

python3 main.py \
    solution.brute_force.enable=false \
    solution.brute_force.save_results=true \
    solution.llm_force.enable=true \
    solution.llm_force.verification=true \
    solution.llm_force.save_results=true

python3 main.py \
    solution.brute_force.enable=true \
    solution.brute_force.save_results=true \
    solution.llm_force.enable=false \
    solution.llm_force.verification=true \
    solution.llm_force.save_results=true