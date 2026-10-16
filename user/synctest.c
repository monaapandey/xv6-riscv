#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

void
test_producer_consumer(void)
{
  printf("\n--- Test 1: Producer / Consumer ---\n");

  int sem_mutex = sem_alloc(1);  // Binary semaphore for critical section
  int sem_full = sem_alloc(0);   // Counts items produced

  int pid = fork();
  if (pid < 0) {
    printf("Fork failed\n");
    exit(1);
  }

  if (pid == 0) {
    // Child: Producer
    for (int i = 1; i <= 3; i++) {
      sem_wait(sem_mutex);
      printf("[Producer] Producing item %d\n", i);
      sem_post(sem_mutex);

      sem_post(sem_full); // Signal item available
      sleep(100);          // Delay to simulate work
    }
    exit(0);
  } else {
    // Parent: Consumer
    for (int i = 1; i <= 3; i++) {
      sem_wait(sem_full); // Wait for item
      sem_wait(sem_mutex);
      printf("[Consumer] Consumed item %d\n", i);
      sem_post(sem_mutex);
    }
    wait(0);
  }

  sem_free(sem_mutex);
  sem_free(sem_full);
  printf("Test 1 Passed!\n");
}

void
test_ordering(void)
{
  printf("\n--- Test 2: Enforced Parent-Child Execution Order ---\n");

  int sem_step1 = sem_alloc(0);
  int sem_step2 = sem_alloc(0);

  int pid = fork();
  if (pid == 0) {
    // Child process runs step 2
    sem_wait(sem_step1); // Must wait for parent to print Step 1
    printf("Child: Executing Step 2\n");
    sem_post(sem_step2); // Unlock step 3 for parent
    exit(0);
  } else {
    // Parent process runs step 1 and step 3
    printf("Parent: Executing Step 1\n");
    sem_post(sem_step1); // Unlock step 2 for child

    sem_wait(sem_step2); // Wait for child to complete step 2
    printf("Parent: Executing Step 3\n");
    wait(0);
  }

  sem_free(sem_step1);
  sem_free(sem_step2);
  printf("Test 2 Passed!\n");
}

int
main(int argc, char *argv[])
{
  printf("Starting Semaphore Synchronization Tests...\n");

  test_producer_consumer();
  test_ordering();

  printf("\nAll Semaphore Tests Completed Successfully!\n");
  exit(0);
}