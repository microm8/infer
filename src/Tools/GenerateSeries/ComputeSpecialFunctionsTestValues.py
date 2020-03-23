# Licensed to the .NET Foundation under one or more agreements.
# The .NET Foundation licenses this file to you under the MIT license.
# See the LICENSE file in the project root for more information.
from __future__ import division
from sympy import *
import sympy.stats
import os
import csv
import mpmath

sx = Symbol('sx')

def normal_cdf_moment_ratio(n, x):
    mpmath.mp.dps = 500
    xmpf = x._to_mpmath(500)
    nmpf = n._to_mpmath(500)
    if x < 0:
        return Float(mpmath.power(2, -0.5 - nmpf / 2) * mpmath.hyperu(nmpf / 2 + 0.5, 0.5, xmpf * xmpf / 2))
    return Float(mpmath.exp(xmpf * xmpf / 4) * mpmath.pcfu(0.5 + nmpf, -xmpf))

def beta_cdf(x, a, b):
    mpmath.ncdf()
    rv = sympy.stats.Beta('p', a, b)
    return sympy.stats.P(rv < x)

def normal_cdf2(x, y, r):
    if x == -oo or y == -oo:
        return Float('0')
    if x == oo:
        return erfc(-y / sqrt(S(2))) / 2
    if y == oo:
        return erfc(-x / sqrt(S(2))) / 2
    mpmath.mp.dps = 500
    xmpf = x._to_mpmath(500)
    ympf = y._to_mpmath(500)
    rmpf = r._to_mpmath(500)
    f = lambda t: mpmath.mpf('0') if t == mpmath.mpf('-1') else 1 / (2 * mpmath.pi * mpmath.sqrt(1 - t * t)) * mpmath.exp(-(xmpf * xmpf + ympf * ympf - 2 * t * xmpf * ympf) / (2 * (1 - t * t)))
    result = mpmath.quad(f, [-1, rmpf])
    return Float(result)

pair_info = {
    'BesselI.csv': besseli,
    'BetaCdf.csv': None, #lambda x, a, b: sympy.stats.P(sympy.stats.Beta('p', a, b) < x),
    'Digamma.csv': digamma,
    'Erfc.csv': erfc,
    'ExpMinus1.csv': lambda x: exp(x) - 1,
    'ExpMinus1RatioMinus1RatioMinusHalf.csv': lambda x: ((exp(x) - 1) / x - 1) / x - S(1) / 2,
    'Gamma.csv': gamma,
    'GammaLn.csv': loggamma,
    'GammaLower.csv': lambda s, x: lowergamma(s, x) / gamma(s) if s != oo else S(0),
    'GammaUpper.csv': uppergamma,
    'GammaUpperRegularized.csv': lambda s, x: 1 - (lowergamma(s, x) / gamma(s) if s != oo else S(0)),
    'GammaUpperScale.csv' : lambda s, x: x ** s * exp(-x) / gamma(s),
    'Log1MinusExp.csv': lambda x: log(1 - exp(x)),
    'Log1Plus.csv': lambda x: log(1 + x),
    'LogExpMinus1.csv': lambda x: log(exp(x) - 1),
    'Logistic.csv': lambda x: 1 / (1 + exp(-x)),
    'logisticGaussian.csv': None, #lambda m, v: integrate(1 / sqrt(2 * pi * v) * exp(-(sx - m) * (sx - m) / (2 * v)) / (1 + exp(-sx)), (sx, -oo, oo)),
    'logisticGaussianDeriv.csv': None,
    'logisticGaussianDeriv2.csv': None,
    'LogisticLn.csv': lambda x: -log(1 + exp(-x)),
    'LogSumExp.csv': lambda x, y: log(exp(x) + exp(y)),
    'NormalCdf.csv': lambda x: erfc(-x / sqrt(S(2))) / 2,
    'NormalCdf2.csv': normal_cdf2, # lambda x, y, r: integrate(1 / (2 * pi * sqrt(1 - sx * sx)) * exp(-(x * x + y * y - 2 * sx * x * y) / (2 * (1 - sx * sx))), (sx, -1, r)),
    'NormalCdfIntegral.csv': None,
    'NormalCdfIntegralRatio.csv': None,
    'NormalCdfInv.csv': lambda x: -sqrt(S(2)) * erfcinv(2 * x),
    'NormalCdfLn.csv': lambda x: log(erfc(-x / sqrt(S(2))) / 2),
    'NormalCdfLn2.csv': None,
    'NormalCdfLogit.csv': lambda x: log(erfc(-x / sqrt(S(2))) / 2) - log(erfc(x / sqrt(S(2))) / 2),
    'NormalCdfMomentRatio.csv': normal_cdf_moment_ratio,
    'NormalCdfRatioLn2.csv': None,
    'Tetragamma.csv': lambda x: polygamma(2, x),
    'Trigamma.csv': trigamma,
    'ulp.csv': None
    }


def float_str_csharp_to_python(s):
    return s.replace('NaN', 'nan').replace('Infinity', 'inf')

def float_str_python_to_csharp(s):
    return s.replace('nan', 'NaN').replace('inf', 'Infinity')

dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', 'test', 'Tests', 'data', 'SpecialFunctionsValues')
with os.scandir(dir) as it:
    for entry in it:
        if entry.name.endswith('.csv') and entry.is_file():
            print(f'Processing {entry.name}...')
            if entry.name not in pair_info.keys() or pair_info[entry.name] == None:
                print("Don't know how to process. Skipping.")
                continue
            f = pair_info[entry.name]
            with open(entry.path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',')
                fieldnames = reader.fieldnames
                arg_count = (len(fieldnames) - 1) // 2
                newrows = []
                for row in reader:
                    newrow = dict(row)
                    args = []
                    for i in range(arg_count):
                        args.append(Float(float_str_csharp_to_python(row[f'arg{i}exact']), 500))
                    result_in_file = row['expectedresult']
                    if result_in_file == 'Infinity' or result_in_file == '-Infinity' or result_in_file == 'NaN':
                        newrow['expectedresult'] = result_in_file
                    else:
                        try:
                            result = f(*args).evalf(50, maxn=500)
                        except ValueError:
                            print(f'ValueError for args {args}. Setting result to NaN.')
                            result = Float('nan')
                        newrow['expectedresult'] = float_str_python_to_csharp(str(result))
                    newrows.append(newrow)

            with open(entry.path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                writer.writerows(newrows)