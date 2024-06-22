#!/usr/bin/env python3

import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.power import FTestAnovaPower
import pandas as pd
import numpy as np
import

def estimate_sample_size(effect_size, power=0.8, alpha=0.05, num_groups=3):
    ftester = FTestAnovaPower()
    sample_size = ftester.solve_power(
        effect_size=np.sqrt(cohens_f_squared(effect_size)),
        power=power,
        alpha=alpha,
        k_groups=num_groups
    )
    return int(np.ceil(sample_size))
