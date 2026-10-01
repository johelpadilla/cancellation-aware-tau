"""Cancellation-aware order coherence: decomposition of absolute concordance change."""
from .tau import tau_b_matrix, null_var_tau_b, untied_null_var, sign_vectors
from .decomposition import (operator_F, decompose, power_mean_change,
                            restricted_signed_relation, identity, signed_change, abs_change)
from .calibration import (window_edge_values, conformal_scores, conformal_pvalue,
                          stat_D, stat_abs_mean, analytic_null_guide,
                          circular_shift_record)
from .simulate import Model, build_model, simulate

__version__ = "1.0.0"
