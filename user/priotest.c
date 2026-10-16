#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

void cpu_work(void) {
  volatile int x = 0;
  for (int i = 0; i < 50000000; i++) {
    x = x + (i * 3) % 100;
  }
}

int main(void) {
  // Priority 1 (Highest) se 10 (Lowest) tak test karenge
  int priorities[4] = {1, 4, 7, 10}; 
  int pids[4];

  printf("Starting Priority Scheduler Test...\n");

  for (int i = 0; i < 4; i++) {
    pids[i] = fork();
    if (pids[i] == 0) {
      // Child process
      int my_pid = getpid();
      set_priority(my_pid, priorities[i]);
      
      printf("Child %d (PID: %d) started with priority %d\n", i + 1, my_pid, priorities[i]);
      
      cpu_work(); // CPU ka time consume karo

      printf("Child %d (PID: %d) finished!\n", i + 1, my_pid);
      exit(0);
    }
  }

  // Parent process charo bacchon ka wait karegi
  for (int i = 0; i < 4; i++) {
    wait(0);
  }

  printf("Priority Test completed.\n");
  exit(0);
}