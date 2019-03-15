import random


def chi_squared(results):
    n = 100.0
    r = 10.0
    chi = 0
    for result in results:
        chi += (result[1] - (n / r)) ** 2
    chi = chi * (r / n)
    print("Chi-squared Score: " + str(abs(chi - r)))
    print("Range: " + str(round(2 * (r ** (1.0 / 2)), 1)) + "\n")


def mc_method(u, a, b, m):
    random_nums = []
    for i in range(100):
        u = float((b * u + a) % m)
        r = u / m
        random_nums.append(r)
    freq = get_frequencies(random_nums)
    chi_squared(freq)


def standard_generator():
    random_nums = []
    for i in range(100):
        r = random.random()
        random_nums.append(r)
    freq = get_frequencies(random_nums)
    chi_squared(freq)


def get_frequencies(nums):
    frequencies = []
    for i in range(10):
        count = sum(float(i) / 10 < element < float(i + 1) / 10 for element in nums)
        frequencies.append([i, count])
    return frequencies


if __name__ == '__main__':
    mc_method(1435, 534, 934, 453)
    standard_generator()
