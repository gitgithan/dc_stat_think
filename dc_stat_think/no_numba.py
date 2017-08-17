# -*- coding: utf-8 -*-

"""Utilities for DataCamp's statistical thinking courses."""

import numpy as np
import numba


def ecdf_formal(x, data):
    """
    Compute the values of the formal ECDF generated from `data` at x.
    I.e., if F is the ECDF, return F(x).

    Parameters
    ----------
    x : int, float, or array_like
        Positions at which the formal ECDF is to be evaluated.
    data : array_like
        One-dimensional array of data to use to generate the ECDF.

    Returns
    -------
    output : float or ndarray
        Value of the ECDF at `x`.
    """
    # Remember if the input was scalar
    if np.isscalar(x):
        return_scalar = True
    else:
        return_scalar = False

    # If x has any nans, raise a RuntimeError
    if np.isnan(x).any():
        raise RuntimeError('Input cannot have NaNs.')

    # Convert x to array
    x = _convert_data(x, inf_ok=True)

    # Convert data to sorted NumPy array with no nan's
    data = _convert_data(data, inf_ok=True)

    # Compute formal ECDF value
    out = _ecdf_formal(x, np.sort(data))

    if return_scalar:
        return out[0]
    return out


# @numba.jit(nopython=True)
def _ecdf_formal(x, data):
    """
    Compute the values of the formal ECDF generated from `data` at x.
    I.e., if F is the ECDF, return F(x).

    Parameters
    ----------
    x : array_like
        Positions at which the formal ECDF is to be evaluated.
    data : array_like
        *Sorted* data set to use to generate the ECDF.

    Returns
    -------
    output : float or ndarray
        Value of the ECDF at `x`.
    """
    output = np.empty_like(x)

    for i, x_val in enumerate(x):
        if np.isnan(x_val):
            output[i] = np.nan
        else:
            j = 0
            while j < len(data) and x_val >= data[j]:
                j += 1

            output[i] = j

    return output / len(data)


def ecdf(data, formal=False, buff=0.1, min_x=None, max_x=None):
    """
    Generate `x` and `y` values for plotting an ECDF.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data to be plotted as an ECDF.
    formal : bool, default False
        If True, generate `x` and `y` values for formal ECDF.
        Otherwise, generate `x` and `y` values for "dot" style ECDF.
    buff : float, default 0.1
        How long the tails at y = 0 and y = 1 should extend as a
        fraction of the total range of the data. Ignored if
        `formal` is False.
    min_x : float, default None
        Minimum value of `x` to include on plot. Overrides `buff`.
        Ignored if `formal` is False.
    max_x : float, default None
        Maximum value of `x` to include on plot. Overrides `buff`.
        Ignored if `formal` is False.

    Returns
    -------
    x : array
        `x` values for plotting
    y : array
        `y` values for plotting

    Notes
    -----
    .. nan entries in `data` are ignored.
    """
    if formal and buff is None and (min_x is None or max_x is None):
        raise RunetimeError(
                    'If `buff` is None, `min_x` and `max_x` must be specified.')

    data = _convert_data(data)

    if formal:
        return _ecdf_formal_for_plotting(data, buff=buff, min_x=min_x,
                                         max_x=max_x)
    else:
        return _ecdf_dots(data)


# @numba.jit(nopython=True)
def _ecdf_dots(data):
    """
    Compute `x` and `y` values for plotting an ECDF.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data to be plotted as an ECDF.

    Returns
    -------
    x : array
        `x` values for plotting
    y : array
        `y` values for plotting
    """
    return np.sort(data), np.arange(1, len(data)+1) / len(data)


# @numba.jit(nopython=True)
def _ecdf_formal_for_plotting(data, buff=0.1, min_x=None, max_x=None):
    """
    Generate `x` and `y` values for plotting a formal ECDF.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data to be plotted as an ECDF.
    buff : float, default 0.1
        How long the tails at y = 0 and y = 1 should extend as a fraction
        of the total range of the data.
    min_x : float, default None
        Minimum value of `x` to include on plot. Overrides `buff`.
    max_x : float, default None
        Maximum value of `x` to include on plot. Overrides `buff`.

    Returns
    -------
    x : array
        `x` values for plotting
    y : array
        `y` values for plotting
    """
    # Get x and y values for data points
    x, y = _ecdf_dots(data)

    # Set defaults for min and max tails
    if min_x is None:
        min_x = x[0] - (x[-1] - x[0])*buff
    if max_x is None:
        max_x = x[-1] + (x[-1] - x[0])*buff

    # Set up output arrays
    x_formal = np.empty(2*(len(x) + 1))
    y_formal = np.empty(2*(len(x) + 1))

    # y-values for steps
    y_formal[:2] = 0
    y_formal[2::2] = y
    y_formal[3::2] = y

    # x- values for steps
    x_formal[0] = min_x
    x_formal[1] = x[0]
    x_formal[2::2] = x
    x_formal[3:-1:2] = x[1:]
    x_formal[-1] = max_x

    return x_formal, y_formal


def bootstrap_replicate_1d(data, func, args=()):
    """
    Generate a bootstrap replicate out of `data` using `func`.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data.
    func : function
        Function, with call signature `func(data, *args)` to compute
        replicate statistic from resampled `data`.
    args : tuple, default ()
        Arguments to be passed to `func`.

    Returns
    -------
    output : float
        A bootstrap replicate computed from `data` using `func`.

    Notes
    -----
    .. nan values are ignored.
    """
    data = _convert_data(data, inf_ok=True, min_len=1)

    return func(np.random.choice(data, size=len(data)))


def draw_bs_reps(data, func, args=(), size=1):
    """
    Generate bootstrap replicates out of `data` using `func`.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data.
    func : function
        Function, with call signature `func(data, *args)` to compute
        replicate statistic from resampled `data`.
    args : tuple, default ()
        Arguments to be passed to `func`.
    size : int, default 1
        Number of bootstrap replicates to generate.

    Returns
    -------
    output : ndarray
        Bootstrap replicates computed from `data` using `func`.

    Notes
    -----
    .. nan values are ignored.
    """
    data = _convert_data(data)

    if args == ():
        if func == np.mean:
            return _draw_bs_reps_mean(data, size=size)
        elif func == np.median:
            return _draw_bs_reps_median(data, size=size)
        elif func == np.std:
            return _draw_bs_reps_std(data, size=size)

    # Make Numba'd function
    f = _make_one_arg_numba_func(func)

    # @numba.jit
    def _draw_bs_reps(data):
        # Set up output array
        bs_reps = np.empty(size)

        # Draw replicates
        n = len(data)
        for i in range(size):
            bs_reps[i] = f(np.random.choice(data, size=n), args)

        return bs_reps

    return _draw_bs_reps(data)


# @numba.jit(nopython=True)
def _draw_bs_reps_mean(data, size=1):
    """
    Generate bootstrap replicates of the mean out of `data`.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data.
    size : int, default 1
        Number of bootstrap replicates to generate.

    Returns
    -------
    output : float
        Bootstrap replicates of the mean computed from `data`.
    """
    # Set up output array
    bs_reps = np.empty(size)

    # Draw replicates
    n = len(data)
    for i in range(size):
        bs_reps[i] = np.mean(np.random.choice(data, size=n))

    return bs_reps


# @numba.jit(nopython=True)
def _draw_bs_reps_median(data, size=1):
    """
    Generate bootstrap replicates of the median out of `data`.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data.
    size : int, default 1
        Number of bootstrap replicates to generate.

    Returns
    -------
    output : float
        Bootstrap replicates of the median computed from `data`.
    """
    # Set up output array
    bs_reps = np.empty(size)

    # Draw replicates
    n = len(data)
    for i in range(size):
        bs_reps[i] = np.median(np.random.choice(data, size=n))

    return bs_reps


# @numba.jit(nopython=True)
def _draw_bs_reps_std(data, ddof=0, size=1):
    """
    Generate bootstrap replicates of the median out of `data`.

    Parameters
    ----------
    data : array_like
        One-dimensional array of data.
    ddof : int
        Delta degrees of freedom. Divisor in standard deviation
        calculation is `len(data) - ddof`.
    size : int, default 1
        Number of bootstrap replicates to generate.

    Returns
    -------
    output : float
        Bootstrap replicates of the median computed from `data`.
    """
    # Set up output array
    bs_reps = np.empty(size)

    # Draw replicates
    n = len(data)
    for i in range(size):
        bs_reps[i] = np.std(np.random.choice(data, size=n))

    if ddof > 0:
        return bs_reps * np.sqrt(n / (n - ddof))

    return bs_reps


def draw_bs_pairs_linreg(x, y, size=1):
    """
    Perform pairs bootstrap for linear regression.

    Parameters
    ----------
    x : array_like
        x-values of data.
    y : array_like
        y-values of data.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    slope_reps : ndarray
        Pairs bootstrap replicates of the slope.
    intercept_reps : ndarray
        Pairs bootstrap replicates of the intercept.

    Notes
    -----
    .. Entries where either `x` or `y` has a nan are ignored.
    .. It is possible that a pairs bootstrap sample has the
       same pair over and over again. In this case, a linear
       regression cannot be computed. The pairs bootstrap
       replicate in this instance is NaN.
    """
    x, y = _convert_two_data(x, y, inf_ok=False, min_len=2)

    if np.isclose(x, y).all():
        raise RuntimeError('All x and y values are equal, cannot do regression')

    return _draw_bs_pairs_linreg(x, y, size=size)


# @numba.jit(nopython=True)
def _draw_bs_pairs_linreg(x, y, size=1):
    """
    Perform pairs bootstrap for linear regression.

    Parameters
    ----------
    x : array_like
        x-values of data.
    y : array_like
        y-values of data.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    slope_reps : ndarray
        Pairs bootstrap replicates of the slope.
    intercept_reps : ndarray
        Pairs bootstrap replicates of the intercept.

    Notes
    -----
    .. It is possible that a pairs bootstrap sample ends up with a
       poorly-conditioned least squares problem. The pairs bootstrap
       replicate in this instance is NaN.
    """
    # Set up array of indices to sample from
    inds = np.arange(len(x))

    # Initialize samples
    bs_slope_reps = np.empty(size)
    bs_intercept_reps = np.empty(size)

    # Take samples
    for i in range(size):
        bs_inds = np.random.choice(inds, len(inds))
        bs_x, bs_y = x[bs_inds], y[bs_inds]

        # Construct and scale least squares problem
        A = np.stack((bs_x, np.ones(len(bs_x)))).transpose()
        A2 = A * A
        scale = np.sqrt(np.array([np.sum(A2[:,0]), np.sum(A2[:,1])]))
        A /= scale

        # Solve
        c, resids, rank, s = np.linalg.lstsq(A, bs_y)

        # Return NaN if poorly conditioned
        if rank == 2:
            bs_slope_reps[i], bs_intercept_reps[i] = (c.T / scale).T
        else:
            bs_slope_reps[i], bs_intercept_reps[i] = np.nan, np.nan

    return bs_slope_reps, bs_intercept_reps


def draw_bs_pairs(x, y, func, args=(), size=1):
    """
    Perform pairs bootstrap for single statistic.

    Parameters
    ----------
    x : array_like
        x-values of data.
    y : array_like
        y-values of data.
    func : function
        Function, with call signature `func(x, y, *args)` to compute
        replicate statistic from pairs bootstrap sample. It must return
        a single, scalar value.
    args : tuple, default ()
        Arguments to be passed to `func`.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    output : ndarray
        Bootstrap replicates.
    """
    x, y = _convert_two_data(x, y, min_len=1)

    # Make Numba'd function
    f = _make_two_arg_numba_func(func)

    n = len(x)

    # @numba.jit
    def _draw_bs_pairs(x, y):
        # Set up array of indices to sample from
        inds = np.arange(n)

        # Initialize replicates
        bs_replicates = np.empty(size)

        # Generate replicates
        for i in range(size):
            bs_inds = np.random.choice(inds, n)
            bs_x, bs_y = x[bs_inds], y[bs_inds]
            bs_replicates[i] = f(bs_x, bs_y, args)

        return bs_replicates

    return _draw_bs_pairs(x, y)


def permutation_sample(data_1, data_2):
    """
    Generate a permutation sample from two data sets. Specifically,
    concatenate `data_1` and `data_2`, scramble the order of the
    concatenated array, and then return the first len(data_1) entries
    and the last len(data_2) entries.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    out_1 : ndarray, same shape as `data_1`
        Permutation sample corresponding to `data_1`.
    out_2 : ndarray, same shape as `data_2`
        Permutation sample corresponding to `data_2`.
    """
    data_1 = _convert_data(data_1)
    data_2 = _convert_data(data_2)

    return _permutation_sample(data_1, data_2)


# @numba.jit(nopython=True)
def _permutation_sample(data_1, data_2):
    """
    Generate a permutation sample from two data sets. Specifically,
    concatenate `data_1` and `data_2`, scramble the order of the
    concatenated array, and then return the first len(data_1) entries
    and the last len(data_2) entries.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    out_1 : ndarray, same shape as `data_1`
        Permutation sample corresponding to `data_1`.
    out_2 : ndarray, same shape as `data_2`
        Permutation sample corresponding to `data_2`.
    """
    x = np.concatenate((data_1, data_2))
    np.random.shuffle(x)
    return x[:len(data_1)], x[len(data_1):]


def draw_perm_reps(data_1, data_2, func, args=(), size=1):
    """
    Generate permutation replicates of `func` from `data_1` and
    `data_2`

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.
    func : function
        Function, with call signature `func(x, y, *args)` to compute
        replicate statistic from permutation sample. It must return
        a single, scalar value.
    args : tuple, default ()
        Arguments to be passed to `func`.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    output : ndarray
        Permutation replicates.
    """
    # Convert to Numpy arrays
    data_1 = _convert_data(data_1)
    data_2 = _convert_data(data_2)

    if args == ():
        if func == diff_of_means:
            return _draw_perm_reps_diff_of_means(data_1, data_2, size=size)
        elif func == studentized_diff_of_means:
            return _draw_perm_reps_studentized_diff_of_means(data_1, data_2,
                                                             size=size)

    # Make a Numba'd function for drawing reps.
    f = _make_two_arg_numba_func(func)

    # @numba.jit
    def _draw_perm_reps(data_1, data_2):
        n1 = len(data_1)
        x = np.concatenate((data_1, data_2))

        perm_reps = np.empty(size)
        for i in range(size):
            np.random.shuffle(x)
            perm_reps[i] = f(x[:n1], x[n1:], args)

        return perm_reps

    return _draw_perm_reps(data_1, data_2)


# @numba.jit(nopython=True)
def _draw_perm_reps_diff_of_means(data_1, data_2, size=1):
    """
    Generate permutation replicates of difference of means from
    `data_1` and `data_2`

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    output : ndarray
        Permutation replicates.
    """
    n1 = len(data_1)
    x = np.concatenate((data_1, data_2))

    perm_reps = np.empty(size)
    for i in range(size):
        np.random.shuffle(x)
        perm_reps[i] = _diff_of_means(x[:n1], x[n1:])

    return perm_reps


# @numba.jit(nopython=True)
def _draw_perm_reps_studentized_diff_of_means(data_1, data_2, size=1):
    """
    Generate permutation replicates of Studentized difference
    of means from  `data_1` and `data_2`

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.
    size : int, default 1
        Number of pairs bootstrap replicates to draw.

    Returns
    -------
    output : ndarray
        Permutation replicates.
    """
    n1 = len(data_1)
    x = np.concatenate((data_1, data_2))

    perm_reps = np.empty(size)
    for i in range(size):
        np.random.shuffle(x)
        perm_reps[i] = _studentized_diff_of_means(x[:n1], x[n1:])

    return perm_reps


def diff_of_means(data_1, data_2):
    """
    Difference in means of two arrays.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        np.mean(data_1) - np.mean(data_2)
    """
    data_1 = _convert_data(data_1)
    data_2 = _convert_data(data_2)

    return _diff_of_means(data_1, data_2)


# @numba.jit(nopython=True)
def _diff_of_means(data_1, data_2):
    """
    Difference in means of two arrays.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        np.mean(data_1) - np.mean(data_2)
    """
    return np.mean(data_1) - np.mean(data_2)


def studentized_diff_of_means(data_1, data_2):
    """
    Studentized difference in means of two arrays.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        Studentized difference of means.

    Notes
    -----
    .. If the variance of both `data_1` and `data_2` is zero, returns
       np.nan.
    """
    data_1 = _convert_data(data_1)
    data_2 = _convert_data(data_2)

    return _studentized_diff_of_means(data_1, data_2)


# @numba.jit(nopython=True)
def _studentized_diff_of_means(data_1, data_2):
    """
    Studentized difference in means of two arrays.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        Studentized difference of means.

    Notes
    -----
    .. If the variance of both `data_1` and `data_2` is zero, returns
       np.nan.
    """

    denom = np.sqrt(np.var(data_1) / (len(data_1) - 1)
                    + np.var(data_2) / (len(data_2) - 1))

    if denom == 0.0:
        return np.nan

    return (np.mean(data_1) - np.mean(data_2)) / denom


def pearson_r(data_1, data_2):
    """
    Compute the Pearson correlation coefficient between two samples.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        The Pearson correlation coefficient between `data_1`
        and `data_2`.
    """
    x, y = _convert_two_data(data_1, data_2, inf_ok=False, min_len=2)

    return _pearson_r(x, y)


# @numba.jit(nopython=True)
def _pearson_r(x, y):
    """
    Compute the Pearson correlation coefficient between two samples.

    Parameters
    ----------
    data_1 : array_like
        One-dimensional array of data.
    data_2 : array_like
        One-dimensional array of data.

    Returns
    -------
    output : float
        The Pearson correlation coefficient between `data_1`
        and `data_2`.
    """
    return (np.mean(x*y) - np.mean(x) * np.mean(y)) / np.std(x) / np.std(y)


def ks_stat(data_1, data_2):
    """
    Compute the 2-sample Kolmogorov-Smirnov statistic.

    Parameters
    ----------
    data_1 : ndarray
        One-dimensional array of data.
    data_2 : ndarray
        One-dimensional array of data.

    Returns
    -------
    output : float
        Two-sample Kolmogorov-Smirnov statistic.
    """
    data_1 = _convert_data(data_1)
    data_2 = _convert_data(data_2)

    # Sort data_2, necessary for using Numba'd _ecdf_formal
    data_2 = np.sort(data_2)

    return _ks_stat(data_1, data_2)


# @numba.jit(nopython=True)
def _ks_stat(data1, data2):
    """
    Compute the 2-sample Kolmogorov-Smirnov statistic.

    Parameters
    ----------
    data_1 : ndarray
        One-dimensional array of data.
    data_2 : ndarray
        One-dimensional array of data. *Must be sorted.*

    Returns
    -------
    output : float
        Two-sample Kolmogorov-Smirnov statistic.
    """
    # Compute ECDF from data
    x, y = _ecdf_dots(data1)

    # Compute corresponding values of the target CDF
    cdf = _ecdf_formal(x, data2)

    # Compute distances between convex corners and CDF
    D_top = y - cdf

    # Compute distance between concave corners and CDF
    D_bottom = cdf - y + 1/len(data1)

    return np.max(np.concatenate((D_top, D_bottom)))


def draw_ks_reps(n, func, args=(), size=10000, n_reps=1):
    """
    Draw Kolmogorov-Smirnov replicates.

    Parameters
    ----------
    n : int
        Size of experimental sample.
    func : function
        Function with call signature `func(*args, size=1)` that
        generates random number drawn from target distribution.
    args : tuple, default ()
        Arguments to be passed to `func`.
    size : int, default 10000
        Number of random numbers to draw from target distribution
        to approximate its analytical distribution.
    n_reps : int, default 1
        Number of pairs Kolmogorov-Smirnov replicates to draw.

    Returns
    -------
    output : ndarray
        Array of Kolmogorov-Smirnov replicates.
    """
    if func == np.random.exponential:
        return _draw_ks_reps_exponential(n, *args, size=size, n_reps=n_reps)
    elif func == np.random.normal:
        return _draw_ks_reps_normal(n, *args, size=size, n_reps=n_reps)

    # Generate samples from target distribution
    x_f = np.sort(func(*args, size=size))

    # Initialize K-S replicates
    reps = np.empty(n_reps)

    # Draw replicates
    for i in range(n_reps):
        x_samp = func(*args, size=n)
        reps[i] = _ks_stat(x_samp, x_f)

    return reps


# @numba.jit(nopython=True)
def _draw_ks_reps_exponential(n, scale, size=10000, n_reps=1):
    """
    Draw Kolmogorov-Smirnov replicates from Exponential distribution.

    Parameters
    ----------
    n : int
        Size of experimental sample.
    scale : float
        Scale parameter (mean) for Exponential distribution.
    size : int, default 10000
        Number of random numbers to draw from Exponential
        distribution to approximate its analytical distribution.
    n_reps : int, default 1
        Number of pairs Kolmogorov-Smirnov replicates to draw.

    Returns
    -------
    output : ndarray
        Array of Kolmogorov-Smirnov replicates.
    """
    # Generate samples from target distribution
    x_f = np.sort(np.random.exponential(scale, size=size))

    # Initialize K-S replicates
    reps = np.empty(n_reps)

    # Draw replicates
    for i in range(n_reps):
        x_samp = np.random.exponential(scale, size=n)
        reps[i] = _ks_stat(x_samp, x_f)

    return reps


# @numba.jit(nopython=True)
def _draw_ks_reps_normal(n, mu, sigma, size=10000, n_reps=1):
    """
    Draw Kolmogorov-Smirnov replicates from Normal distribution.

    Parameters
    ----------
    n : int
        Size of experimental sample.
    mu : float
        Location parameter (mean) of Normal distribution.
    sigma : float
        Scale parameter (std) of Normal distribution.
    size : int, default 10000
        Number of random numbers to draw from Normal
        distribution to approximate its analytical distribution.
    n_reps : int, default 1
        Number of pairs Kolmogorov-Smirnov replicates to draw.

    Returns
    -------
    output : ndarray
        Array of Kolmogorov-Smirnov replicates.
    """
    # Generate samples from target distribution
    x_f = np.sort(np.random.normal(mu, sigma, size=size))

    # Initialize K-S replicates
    reps = np.empty(n_reps)

    # Draw replicates
    for i in range(n_reps):
        x_samp = np.random.normal(mu, sigma, size=n)
        reps[i] = _ks_stat(x_samp, x_f)

    return reps


def _convert_data(data, inf_ok=False, nan_ok=False, min_len=1):
    """
    Convert inputted 1D data set into NumPy array of floats.
    All nan's are dropped.

    Parameters
    ----------
    data : int, float, or array_like
        Input data, to be converted.
    inf_ok : bool, default False
        If True, np.inf values are allowed in the arrays.
    nan_ok : bool, default False
        If True, NaNs can be left in array.
    min_len : int, default 1
        Minimum length of array.

    Returns
    -------
    output : ndarray
        `data` as a one-dimensional NumPy array, dtype float.
    """
    # If it's scalar, convert to array
    if np.isscalar(data):
        data = np.array([data], dtype=np.float)

    # Convert data to NumPy array
    data = np.array(data, dtype=np.float)

    # Make sure it is 1D
    if len(data.shape) != 1:
        raise RuntimeError('`data` must be a 1D array.')

    # Check for infinite entries
    if not inf_ok and np.isinf(data).any():
        raise RuntimeError('All entries must be finite.')

    # Clean out nans
    if not nan_ok:
        data = data[~np.isnan(data)]

    # Check to minimal length
    if len(data) < min_len:
        raise RuntimeError('Array must have at least {0:d} non-NaN entries.'.format(min_len))

    return data


def _convert_two_data(x, y, inf_ok=False, min_len=1):
    """
    Converted two inputted 1D data sets into Numpy arrays of floats.
    Indices where one of the two arrays is nan are dropped.

    Parameters
    ----------
    x : array_like
        Input data, to be converted. `x` and `y` must have the same length.
    y : array_like
        Input data, to be converted. `x` and `y` must have the same length.
    inf_ok : bool, default False
        If True, np.inf values are allowed in the arrays.
    min_len : int, default 1
        Minimum length of array.

    Returns
    -------
    x_out : ndarray
        `x` as a one-dimensional NumPy array, dtype float.
    y_out : ndarray
        `y` as a one-dimensional NumPy array, dtype float.
    """
    # Make sure they are array-like
    if np.isscalar(x) or np.isscalar(y):
        raise RuntimeError('Arrays must be 1D arrays of the same length.')

    # Convert to Numpy arrays
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    # Check for infinite entries
    if not inf_ok and (np.isinf(x).any() or np.isinf(y).any()):
        raise RuntimeError('All entries in arrays must be finite.')

    # Make sure they are 1D arrays
    if len(x.shape) != 1 or len(y.shape) != 1:
        raise RuntimeError('Arrays must be 1D arrays.')

    # Must be the same length
    if len(x) != len(y):
        raise RuntimeError('Arrays must be 1D arrays of the same length.')

    # Clean out nans
    inds = ~np.logical_or(np.isnan(x), np.isnan(y))
    x = x[inds]
    y = y[inds]

    # Check to minimal length
    if len(x) < min_len:
        raise RuntimeError('Arrays must have at least {0:d} mutual non-NaN entries.'.format(min_len))

    return x, y


def _make_one_arg_numba_func(func):
    """
    Make a Numba'd version of a function that takes one positional
    argument.

    Parameters
    ----------
    func : function
        Function with call signature `func(x, *args)`.

    Returns
    -------
    output : Numba'd function
        A Numba'd version of the functon

    Notes
    -----
    .. If the function is Numba'able in nopython mode, it will compile
       in that way. Otherwise, falls back to object mode.
    """
    # @numba.jit
    def f(x, args=()):
        return func(x, *args)
    return f


def _make_two_arg_numba_func(func):
    """
    Make a Numba'd version of a function that takes two positional
    arguments.

    Parameters
    ----------
    func : function
        Function with call signature `func(x, y, *args)`.

    Returns
    -------
    output : Numba'd function
        A Numba'd version of the functon

    Notes
    -----
    .. If the function is Numba'able in nopython mode, it will compile
       in that way. Otherwise, falls back to object mode.
    """
    # @numba.jit
    def f(x, y, args=()):
        return func(x, y, *args)
    return f


def _make_rng_numba_func(func):
    """
    Make a Numba'd version of a function to draw random numbers.

    Parameters
    ----------
    func : function
        Function with call signature `func(*args, size=1)`.

    Returns
    -------
    output : Numba'd function
        A Numba'd version of the functon

    Notes
    -----
    .. If the function is Numba'able in nopython mode, it will compile
       in that way. Otherwise, falls back to object mode.
    """
    # @numba.jit
    def f(args, size=1):
        all_args = args + (size,)
        return func(*all_args)
    return f


# @numba.jit(nopython=True)
def _seed_numba(seed):
    """
    Seed the random number generator for Numba'd functions.

    Parameters
    ----------
    seed : int
        Seed of the RNG.

    Returns
    -------
    None
    """
    np.random.seed(seed)