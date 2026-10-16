#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

#define NUM_THREADS 3
#define ITERATIONS 100000

volatile int counter = 0;

// Thread worker function
void worker(void *arg) {
  for(int i = 0; i < ITERATIONS; i++) {
    counter++; // Shared counter race condition
  }
  exit(0); // RISC-V mein exit() ko integer status chahiye hota hai
}

int main(int argc, char *argv[]) {
  printf("Starting %d threads...\n", NUM_THREADS);

  for(int i = 0; i < NUM_THREADS; i++) {
    // 1. Allocate 4096 bytes (1 Page) for user thread stack
    void *stack = malloc(4096);
    if(stack == 0){
      printf("malloc failed\n");
      exit(1);
    }

    // 2. Call clone: Pass function, argument (0), and allocated stack
    int pid = clone(worker, 0, stack);
    if(pid < 0){
      printf("clone failed\n");
      exit(1);
    }
  }

  // 3. Wait for all threads to finish and prevent memory leaks
  for(int i = 0; i < NUM_THREADS; i++) {
    void *thread_stack;
    
    // RISC-V upgrade: hum stack address wapas receive kar rahe hain
    join(&thread_stack); 
    
    // Memory leak rokne ke liye stack free karna zaroori hai!
    free(thread_stack);
  }

  printf("Final Counter Value: %d (Expected: %d)\n", counter, NUM_THREADS * ITERATIONS);
  printf("NOTE: If Final Value < Expected, Threads are sharing memory (Race Condition Verified!)\n");
  
  exit(0);
}