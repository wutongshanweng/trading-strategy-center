import numpy as np
from scipy import stats


class BayesianInference:
    def __init__(self, prior_mean: float = 0.0, prior_var: float = 1.0, obs_var: float = 1.0):
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.obs_var = obs_var
        self.posterior_mean = prior_mean
        self.posterior_var = prior_var
        self.n = 0

    def update(self, returns: np.ndarray):
        arr = np.asarray(returns, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            return (self.posterior_mean, self.posterior_var)
        n_new = len(arr)
        prior_prec, obs_prec = 1.0 / self.posterior_var, n_new / self.obs_var
        self.posterior_mean = (prior_prec * self.posterior_mean + obs_prec * np.mean(arr)) / (prior_prec + obs_prec)
        self.posterior_var = 1.0 / (prior_prec + obs_prec)
        self.n += n_new
        return (self.posterior_mean, self.posterior_var)

    def get_probability(self):
        if self.posterior_var <= 0:
            return 0.5
        return float(1.0 - stats.norm.cdf(0, loc=self.posterior_mean, scale=np.sqrt(self.posterior_var)))

    def get_credible_interval(self, alpha: float = 0.05):
        if self.posterior_var <= 0:
            return (np.nan, np.nan)
        std = np.sqrt(self.posterior_var)
        return (float(stats.norm.ppf(alpha / 2, loc=self.posterior_mean, scale=std)),
                float(stats.norm.ppf(1 - alpha / 2, loc=self.posterior_mean, scale=std)))
