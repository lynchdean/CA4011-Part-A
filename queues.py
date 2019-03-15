import math
import random
from copy import deepcopy
from datetime import datetime, timedelta

import numpy as np


class Patient:
    def __init__(self, at, g, n=False):
        self.arrival_time = at
        self.gender = g  # m = male, f = female
        self.is_new = n
        self.waited = False #after they wait a set amount of time they might leave

    def __lt__(self, other):
        return self.arrival_time < other.arrival_time


class Server:
    def __init__(self, gp="n", rate=1.0, breaks=None):
        if breaks is None:
            breaks = []
        self.gender_pref = gp  # m = male, f = female, n = no preference
        self.rate = rate
        self.breaks = breaks
        self.free_at = timedelta(minutes=0)


def queue_system(arrivals_list, servers, avg_service_time_per_hour, title=""):
    measures = []
    original_servers = servers
    avg_service_time = timedelta(minutes=60.0 / avg_service_time_per_hour)
    avg_service_time_new = avg_service_time * 2
    for arrivals in arrivals_list:
        servers = []
        for server in original_servers:
            servers.append(deepcopy(server))
        departed = []
        w = []
        wq = []
        idle_mins = [timedelta(minutes=0)] * len(servers)
        server_available = [timedelta(minutes=0)] * len(servers)
        waiting = arrivals.copy()
        while waiting:
            server = find_next_appropraite_server(servers, server_available, waiting[0])[0]
            server_idx = find_next_appropraite_server(servers, server_available, waiting[0])[1]
            # This will always be true for first server but possibly not second or third
            if not waiting:
                break
            # If the server is on break, update server availability
            elif server_has_break(server, server_available[server_idx]):
                server_available[server_idx] += timedelta(minutes=30)  # we can change length of break
                continue
            # Server is waiting for patient to arrive or the patient of the correct gender
            elif server_is_waiting(waiting[0], server_available[server_idx]):
                if waiting[0].is_new:
                    departure_time = (waiting[0].arrival_time + avg_service_time_new * server.rate)
                else:
                    departure_time = (waiting[0].arrival_time + avg_service_time * server.rate)
                idle_mins[server_idx] += waiting[0].arrival_time - server_available[server_idx]
                server_available[server_idx] = departure_time
                if waiting[0].is_new:
                    w.append(avg_service_time_new * server.rate)
                else:
                    w.append(avg_service_time * server.rate)
                wq.append(timedelta(minutes=0))
                departed.append(waiting[0])
                waiting.pop(0)
            # If the patient is of the wrong gender we just have to wait for the next server to come
            else:
                if waiting[0].is_new:
                    departure_time = (server_available[server_idx] + avg_service_time_new * server.rate)
                else:
                    departure_time = (server_available[server_idx] + avg_service_time * server.rate)
                server_available[server_idx] = departure_time
                w.append(server_available[server_idx] - waiting[0].arrival_time)
                if waiting[0].is_new:
                    wq.append(server_available[server_idx] - waiting[0].arrival_time - avg_service_time_new * server.rate)
                else:
                    wq.append(server_available[server_idx] - waiting[0].arrival_time - avg_service_time * server.rate)
                departed.append(waiting[0])
                waiting.pop(0)
        final_time = max(server_available)
        measures.append(daily_measures(final_time, idle_mins, len(servers), w, wq))
    print_measures(title, measures)


def find_next_appropraite_server(servers, server_available, customer):
    shortest_time = timedelta(minutes=-1)
    for server_idx, server in enumerate(servers):
        if server_available[server_idx] < shortest_time or shortest_time == timedelta(minutes=-1): #the next server isn't always the next available
            if correct_gender(customer, server):
                shortest_time = server_available[server_idx]
                position = server_idx

    return [servers[position], position]


def server_has_break(server, current_time):
    if server.breaks != [] and server.breaks[0] <= current_time:
        server.breaks.pop(0)
        return True


def server_is_waiting(patient, server_time):
    return patient.arrival_time > server_time


def correct_gender(patient, server):
    return True if (server.gender_pref == "n") or (patient.gender == server.gender_pref) else False


def daily_measures(final_time, idle_minutes, len_servers, w, wq):
    measures = [average_time_from_list(w), average_time_from_list(wq), max(w), max(wq), [0] * len_servers]
    for i in range(len_servers):
        measures[4][i] = round(idle_minutes[i] / final_time, 2)
    measures.append(average_number_from_list(w, final_time))
    measures.append(average_number_from_list(wq, final_time))
    return measures


def standard_error(t, values):
    error = 0
    for value in values:
        error += (value - t) ** 2

    if error == 0:
        return [0, 0]

    sd = math.sqrt(error/(len(values)))
    se = round(sd/math.sqrt(len(values)), 3)
    return [se, round(sd, 3)]


def mean_and_error(measures, position):
    list_values = [values[position] for values in measures]
    avg_value = round(sum(list_values) / len(list_values), 2)
    errors = standard_error(avg_value, list_values)
    stan_error = errors[0]
    stan_deviation = errors[1]
    return [avg_value, stan_error, stan_deviation]


def max_value(measures, position):  # should we calculate the Standard Error of a max?
    list_values = [values[position] for values in measures]
    return [max(list_values), np.mean(list_values)]


def print_measures(title, measures):
    print(title + " Queue System:")
    w_values = mean_and_error(measures, 0)
    wq_values = mean_and_error(measures, 1)
    w_maxes = max_value(measures, 2)
    wq_maxes = max_value(measures, 3)
    in_system = mean_and_error(measures, 5)
    in_queue = mean_and_error(measures, 6)
    print("Average time (W) a customer spends in the system: " + str(w_values[0]) + " (SE: " + str(w_values[1]) + ")")
    print("Average time (Wq) a customer spends waiting for service: " + str(wq_values[0]) + " (SE: " + str(
        wq_values[1]) + ")")
    print("Maximum time a customer spends in the system: " + str(w_maxes[0]))
    print("Mean maximum time a customer spends in the system in a day: " + str(w_maxes[1]))
    print("Maximum time a customer spends waiting for service: " + str(wq_maxes[0]))
    print("Mean maximum time a customer spends waiting for service: " + str(wq_maxes[1]))
    for i in range(len(measures[0][4])):
        idle_servers = [values[4] for values in measures]
        idle_proportions = mean_and_error(idle_servers, i)
        print("Proportion of time server " + str(i + 1) + " is idle: " + str(idle_proportions[0]) + " (SE: " + str(
            idle_proportions[1]) + ")")
    print("Average number (L) of customers in the system: " + str(in_system[0]) + " (SE: " + str(in_system[1]) + ")")
    print("Average number (Lq) of customers in the queue: " + str(in_queue[0]) + " (SE: " + str(in_queue[1]) + ")")
    print()


def average_time_from_list(times):
    return round((sum(times, timedelta(0, 0)) / len(times)).total_seconds() / 60, 2)


def average_number_from_list(times, final_time):
    return round(sum(times, timedelta(0, 0)) / final_time, 2)


def get_arrivals(calc_method, avg_arr_time, start_time, end_time, replications, chance_new=0.0, new_last=False):
    total_arrivals = []
    time_diff_mins = time_diff_minutes(start_time, end_time)

    for i in range(replications):
        if calc_method == 0:
            arrivals = arrivals_sd(avg_arr_time, time_diff_mins, chance_new)
        else:
            arrivals = arrivals_poisson(avg_arr_time, time_diff_mins, chance_new)

        if new_last:
            sort_new_last(arrivals, avg_arr_time)

        total_arrivals.append(arrivals)

    return total_arrivals


def sort_new_last(arrivals, avg_arr_time):
    mean_interval = timedelta(minutes=float(60) / avg_arr_time)
    pivot = len(arrivals) - 1
    new_time_diffs = []

    i = 0
    while i <= pivot:
        if arrivals[i].is_new:
            if i == 0:
                new_time_diffs.append(arrivals[i].arrival_time - mean_interval)
            else:
                new_time_diffs.append(time_diff_minutes(arrivals[i - 1].arrival_time, arrivals[i].arrival_time))

            arrivals.append(arrivals.pop(i))
            for patient in range(i, pivot):
                arrivals[patient].arrival_time -= mean_interval
            pivot -= 1
        else:
            i += 1

    for time_diff_idx, new_patient_idx in enumerate(range(pivot + 1, len(arrivals))):
        new_time = arrivals[new_patient_idx - 1].arrival_time + new_time_diffs[time_diff_idx]
        arrivals[new_patient_idx].arrival_time = new_time

    return arrivals


def time_diff_minutes(start, end):
    return timedelta(minutes=(end - start).total_seconds() / 60)


def arrivals_poisson(avg_arr_time, time_diff_mins, chance_new):
    arrivals = []
    mean_interval = float(60) / avg_arr_time
    arrival_times = [timedelta(minutes=0)]

    while arrival_times[-1] <= time_diff_mins:
        is_new = random_is_new(chance_new)
        if is_new:
            interval = timedelta(minutes=round(mean_interval + np.random.exponential(mean_interval)))
        else:
            interval = timedelta(minutes=round(np.random.exponential(mean_interval)))

        time = arrival_times[-1] + interval
        arrivals.append(Patient(time, random_gender(), is_new))
        arrival_times.append(time)

    return sorted(arrivals)


def arrivals_sd(avg_arr_time, time_diff_mins, chance_new):
    arrivals = []
    mean_interval = timedelta(minutes=float(60) / avg_arr_time)
    i = mean_interval

    while i <= time_diff_mins:
        is_new = random_is_new(chance_new)
        if is_new:
            time = i + mean_interval + timedelta(minutes=np.round(np.random.normal(0,5)))
        else:
            time = i + timedelta(minutes=np.round(np.random.normal(0,5)))
        i += mean_interval
        arrivals.append(Patient(time, random_gender(), is_new))

    return sorted(arrivals)


def random_gender():
    return "m" if bool(random.getrandbits(1)) == 0 else "f"


def random_is_new(chance_new):
    return True if random.random() <= chance_new else False


# def test_poisson_simulation():
#     mean_arrivals = 6
#     time = timedelta(minutes=60.0)
#     poisson_distribution = [0] * 20
#
#     for i in range(1000):
#         times = arrival_times_poisson(mean_arrivals, time)
#         poisson_distribution[len(times)] += 1
#
#     for i in range(1, 12):
#         r = i
#         print("Predicted Poisson distribution of " + str(i) + " = " + str(
#             round((math.e ** - mean_arrivals) * (mean_arrivals ** r) / (math.factorial(int(r))), 3)))
#         print("Our Poisson distribution of " + str(i) + " = " + str(poisson_distribution[i] / 1000.0))
#         print("\n")


def get_datetime(time):
    fmt = '%H:%M'
    return datetime.strptime(time, fmt)


def main():
    start_time = get_datetime("9:00")
    end_time = get_datetime("17:30")
    avg_arrivals_ph = 8
    avg_services_ph = 3

    '''
    For the first parameter in get_arrivals:
        0 = Standard distribution
        1 = Poisson distribution
    '''

    print("---------------------------------------------------------------------------")
    print("- 2.2.1 Task 1: Compare random and scheduled patterns of customer arrival -")
    print("---------------------------------------------------------------------------\n")
    arrivals_s = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000)
    arrivals_p = get_arrivals(1, avg_arrivals_ph, start_time, end_time, 1000)
    server1 = Server()
    server2 = Server()
    servers = [server1, server2]
    queue_system(arrivals_s, servers, avg_services_ph, "Regular (Standard Distribution)")
    queue_system(arrivals_p, servers, avg_services_ph, "Regular (Poisson)")

    print("---------------------------------------------------------------------------")
    print("-         2.2.2 Task 2: Effect of separate queue for each gender          -")
    print("---------------------------------------------------------------------------\n")
    arrivals_s = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000)
    arrivals_p = get_arrivals(1, avg_arrivals_ph, start_time, end_time, 1000)
    server_m = Server("m")  # Male Server
    server_f = Server("f")  # Female Server
    servers = [server_m, server_f]
    queue_system(arrivals_s, servers, avg_services_ph, "M/F (Standard Distribution)")
    queue_system(arrivals_p, servers, avg_services_ph, "M/F (Poisson)")

    print("---------------------------------------------------------------------------")
    print("-             2.2.3 Task 3: More realistic pattern of service             -")
    print("---------------------------------------------------------------------------\n")
    arrivals = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000)
    break1 = get_datetime("10:45")
    break2 = get_datetime("14:45")
    break3 = get_datetime("11:15")
    break4 = get_datetime("13:15")
    server1_breaks = [time_diff_minutes(start_time, break1), time_diff_minutes(start_time, break2)]
    server2_breaks = [time_diff_minutes(start_time, break3), time_diff_minutes(start_time, break4)]
    server1 = Server("n", 1.0, server1_breaks)  # Regular server with breaks at 10:45 & 14:45
    server2 = Server("n", 1.0, server2_breaks)  # Regular server with breaks at 11:15 & 13:15
    servers = [server1, server2]
    queue_system(arrivals, servers, avg_services_ph, "Breaks (Standard Distribution)")

    print("---------------------------------------------------------------------------")
    print("-                2.2.4 Task 4: Customers not all the same                 -")
    print("---------------------------------------------------------------------------\n")
    arrivals = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000, 0.5, False)
    arrivals_sorted = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000, 0.5, True)
    server1 = Server()
    server2 = Server()
    servers = [server1, server2]
    queue_system(arrivals, servers, avg_services_ph, "Regular & New (Unsorted)")
    queue_system(arrivals_sorted, servers, avg_services_ph, "Regular & New (Sorted)")

    print("---------------------------------------------------------------------------")
    print("-                2.2.5 Task 5: Experience and Inexperience                -")
    print("---------------------------------------------------------------------------\n")
    arrivals = get_arrivals(0, avg_arrivals_ph, start_time, end_time, 1000)
    server1 = Server("n", 1.0)  # Experienced
    server2 = Server("n", 2.0)  # Inexperienced
    server3 = Server("n", 2.0)  # Inexperienced
    servers = [server1, server2, server3]
    queue_system(arrivals, servers, avg_services_ph, "Experienced & Inexperienced")


if __name__ == '__main__':
    main()


