from queues import *

def queue_system(arrivals_list, servers, avg_service_time_per_hour, start_time, output_events ,title=""):
    total_customers_served = []
    total_customers_not_served = []
    events = []
    for arrivals in arrivals_list:
       todays_events = []
       customers_served = 0
       customers_not_served = 0
       for server in servers:
          server.free_at = timedelta(minutes=0) #every day they start off ready to serve customers
       time = timedelta(minutes=5)
       arrivals_list = arrivals.copy()
       queueing = [] #only 3 people can queue at a time
       while arrivals_list != [] or len(queueing) > 0:
          for server in servers:
             if server.free_at <= time:
                if len(queueing) > 0 and server_has_break(server, time) != True:
                   queueing.pop(0)
                   customers_served += 1
                   todays_events.append("At " + str(time + start_time) + " a customer started being served ")
                   server.free_at = time + get_service_time(avg_service_time_per_hour, 5)
          for customer_idx, customer in enumerate(queueing):
             if time - customer.arrival_time >= timedelta(minutes=15) and customer.waited == False: #If they've waited at least 15 minutes
                if customer_idx == 0 and random.random() < 0.1:
                   queueing.pop(customer_idx)
                   customers_not_served += 1
                   todays_events.append("At " + str(time + start_time) + " The customer at the front of the queue left due to waiting too long")
                elif customer_idx == 1 and random.random() < 0.3:
                   queueing.pop(customer_idx)
                   customers_not_served += 1
                   todays_events.append("At " + str(time + start_time) + " The customer in the middle of the queue left due to waiting too long")
                elif customer_idx == 2 and random.random() < 0.5:
                   queueing.pop(customer_idx)
                   customers_not_served += 1
                   todays_events.append("At " + str(time + start_time) + " The customer last in the queue left due to waiting too long")
                customer.waited = True
          for customer in arrivals_list:
             if customer.arrival_time < time: #he enters the shop, this doesn't mean he'll be served
                if len(queueing) < 3: 
                   queueing.append(customer)
                   todays_events.append("At " + str(time + start_time) + " A customer joined the queue")
                else:
                   customers_not_served += 1
                   todays_events.append("At " + str(time + start_time) + " A customer entered the shop but left because it was full")
                arrivals_list.remove(customer)
          for server in servers:
             if server.free_at <= time:
                if len(queueing) > 0 and server_has_break(server, time) != True:
                   queueing.pop(0)
                   customers_served += 1
                   todays_events.append("At " + str(time + start_time) + " a customer started being served ")
                   server.free_at = time + get_service_time(avg_service_time_per_hour, 5)
          time += timedelta(minutes=5)
       total_customers_served.append(customers_served)
       total_customers_not_served.append(customers_not_served)
       events.append(todays_events)
    display_results(total_customers_served,total_customers_not_served, events, output_events)


def display_results(served, not_served, events, output_events):
   if output_events == True:
      for day in events:
         print("Todays events")
         for event in day:
            print(event)
         print("\n")

   proportion_served = []
   for i in range(len(served)):
      percentage = float(served[i])/(served[i] + not_served[i])
      proportion_served.append(percentage)
   mean = round(sum(proportion_served)/len(proportion_served),3)
   errors = standard_error(mean, proportion_served)
   print("Mean Proportion Served: " + str(mean))
   print("Standard Deviation: " + str(errors[1]))
   print("Standard Error: " + str(errors[0]))
   print()

def server_has_break(server, time):
   if server.breaks != [] and server.breaks[0] <= time:
      server.breaks.pop(0)
      server.free_at = time + timedelta(minutes=30) #every break is 30 minutes in examples, will have to change if peoples' breaks are different lengths
      return True 
   return False

def get_service_time(hourly_rate, sd):
    return timedelta(minutes=60.0 / hourly_rate) + timedelta(minutes=np.random.normal(0,5))
    

def main():
    opening_time = timedelta(hours=9.5) #This time is soley used to display events
    shop_start = "10:00"
    lunch_start = "12:00"
    lunch_end = "13:45"
    shop_end = "17:00"
    fmt = '%H:%M'
    start_time = datetime.strptime(shop_start, fmt)
    lunch_start_time = datetime.strptime(lunch_start, fmt)
    lunch_end_time = datetime.strptime(lunch_end, fmt)
    end_time = datetime.strptime(shop_end, fmt)
    before_lunch_arrivals = get_arrivals(1, 6, start_time, lunch_start_time, 400)  # for the first argument, 0 is SD and 1 is poisson
    lunch_arrivals = get_arrivals(1, 12, lunch_start_time, lunch_end_time, 400)
    after_lunch_arrivals = get_arrivals(1, 6, lunch_end_time, end_time, 400)
    
    arrivals = []
    for i in range(len(lunch_arrivals)):
       arrivals.append(list(before_lunch_arrivals[i]))
       for customer in lunch_arrivals[i]:
          customer.arrival_time += before_lunch_arrivals[i][-1].arrival_time
          arrivals[i].append(customer)

    for i in range(len(lunch_arrivals)):   
       for customer in after_lunch_arrivals[i]:
          customer.arrival_time += lunch_arrivals[i][-1].arrival_time
          arrivals[i].append(customer)
    

    avg_service_time_per_hour = 3 #this will be combined with a standard deviation of 5 minutes
    server1_break1 = datetime.strptime("11:00", fmt)
    server2_break1 = datetime.strptime("11:30", fmt)
    server3_break1 = datetime.strptime("14:00", fmt)
    #server4_break1 = datetime.strptime("14:30", fmt)
    server1_breaks = [time_diff_minutes(start_time, server1_break1)] 
    server2_breaks = [time_diff_minutes(start_time, server2_break1)]
    server3_breaks = [time_diff_minutes(start_time, server3_break1)]
    #server4_breaks = [time_diff_minutes(start_time, server4_break1)]
    serv_1 = Server("n", server1_breaks)
    serv_2 = Server("n", server2_breaks)
    serv_3 = Server("n", server3_breaks)
    #serv_4 = Server("n", server3_breaks)
    servers = [serv_1, serv_2, serv_3] #you can add sev_4 here to test the effect a fourth barber would have
    queue_system(arrivals, servers, avg_service_time_per_hour, opening_time, False, "Barber") #True outputs the events of the day

if __name__ == '__main__':
    main()
