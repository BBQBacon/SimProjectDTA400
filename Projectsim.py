import simpy
import random
import matplotlib.pyplot as plt

# Simulation parameters
RANDOM_SEED = 2
INTER_ARRIVAL_MEAN = 2  # Mean time between customer arrivals (minutes)
SERVICE_TIME_MEAN = 4  # Mean service time (minutes)
NUM_CHECKOUT_LANES = 3  # Number of checkout lanes
MAX_QUEUE = 10  # Max queue size to open a new lane
SIMULATION_TIME = 600  # Total simulation time (minutes)

class GroceryStore:
    def __init__(self, env, service_time_mean):
        self.env = env
        self.service_time_mean = service_time_mean
        self.checkout_lanes = [simpy.Resource(env) for _ in range(NUM_CHECKOUT_LANES)]
        self.active_lanes = 1
        self.waiting_times = []
        self.service_times = []
        self.average_queue_lengths = []
        self.queue_record_times = []

    def checkout_customer(self, customer_id, lane_number):
        service_time = random.expovariate(1.0 / self.service_time_mean)
        yield self.env.timeout(service_time)
        print(f"Customer {customer_id} checked out at lane {lane_number + 1} in {service_time:.2f} minutes.")
        self.service_times.append(service_time)

    def add_waiting_time(self, waiting_time):
        self.waiting_times.append(waiting_time)

    def manage_checkouts(self):
        if self.checkout_lanes[0].count + len(self.checkout_lanes[0].queue) >= MAX_QUEUE:
            print(f"Lane 2 opens at time {self.env.now:.2f}")
            self.active_lanes = 2
        if self.active_lanes >= 2 and self.checkout_lanes[1].count + len(self.checkout_lanes[1].queue) >= MAX_QUEUE:
            self.active_lanes = 3
            print(f"Lane 3 opens at time {self.env.now:.2f}")

    def update_queue_stats(self):
        total_queue_length = sum(len(lane.queue) + lane.count for lane in self.checkout_lanes[:self.active_lanes])
        average_queue_length = total_queue_length / self.active_lanes
        self.average_queue_lengths.append(average_queue_length)
        self.queue_record_times.append(self.env.now)

def customer(env, customer_id, store):
    arrival_time = env.now
    print(f"Customer {customer_id} arrives at {arrival_time:.2f} minutes.")
    
    store.manage_checkouts()
    store.update_queue_stats()

    lane_number = min(
        range(store.active_lanes),  # only consider active lanes
        key=lambda i: len(store.checkout_lanes[i].queue) + store.checkout_lanes[i].count
    )
    queue_length = len(store.checkout_lanes[lane_number].queue) + store.checkout_lanes[lane_number].count
    print(f"Customer {customer_id} joins lane {lane_number + 1} with {queue_length} people in queue.")

    with store.checkout_lanes[lane_number].request() as request:
        yield request
        waiting_time = env.now - arrival_time
        store.add_waiting_time(waiting_time)
        print(f"Customer {customer_id} waited for {waiting_time:.2f} minutes at lane {lane_number + 1}.")
        yield env.process(store.checkout_customer(customer_id, lane_number))

def setup(env, store, inter_arrival_mean):
    customer_id = 0
    while env.now < SIMULATION_TIME:
        yield env.timeout(random.expovariate(1.0 / inter_arrival_mean))
        customer_id += 1
        env.process(customer(env, customer_id, store))

# Initialize simulation environment
random.seed(RANDOM_SEED)
env = simpy.Environment()
store_instance = GroceryStore(env, SERVICE_TIME_MEAN)
env.process(setup(env, store_instance, INTER_ARRIVAL_MEAN))
env.run(until=SIMULATION_TIME)
# Plot results
figure, axis = plt.subplots(3, 1, figsize=(8, 12))

# Plot histogram of waiting times
axis[0].hist(store_instance.waiting_times, bins=10, color='blue', edgecolor='black')
axis[0].set_title('Waiting Time Distribution', fontweight="bold")
axis[0].set_xlabel('Waiting Time (minutes)', fontweight="bold")
axis[0].set_ylabel('Frequency', fontweight="bold")
axis[0].grid(True)

# Plot histogram of service times
axis[1].hist(store_instance.service_times, bins=10, color='green', edgecolor='black')
axis[1].set_title('Service Time Distribution', fontweight="bold")
axis[1].set_xlabel('Service Time (minutes)', fontweight="bold")
axis[1].set_ylabel('Frequency', fontweight="bold")
axis[1].grid(True)

# Plot average queue length over time
axis[2].plot(store_instance.queue_record_times, store_instance.average_queue_lengths, color='red')
axis[2].set_title('Average Queue Length over Time', fontweight="bold")
axis[2].set_xlabel('Time (minutes)', fontweight="bold")
axis[2].set_ylabel('Average Queue Length', fontweight="bold")
axis[2].grid(True)

# Adjust layout to prevent overlap
plt.tight_layout()
plt.show()
