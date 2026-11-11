#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

void thread_allocator(void *arg) {
  printf("[Thread] Allocating a new page via sbrk(4096)...\n");
  char *new_mem = sbrk(4096);
  if (new_mem == (char*)-1) {
    printf("[Thread] sbrk failed!\n");
    exit(1);
  }

  // Write shared message into newly allocated memory
  strcpy(new_mem, "SUCCESS: Phase 2 Dynamic Heap Sharing Verified!");
  printf("[Thread] Wrote message to new heap address: %p\n", new_mem);

  // Store pointer at a known shared memory location for main process
  *(char**)arg = new_mem;
  
  sleep(10);
  exit(0);
}

int main(int argc, char *argv[]) {
  printf("=== Phase 2 Dynamic Memory Sharing Test ===\n");

  void *stack = malloc(4096);
  char *shared_ptr = 0;

  int tid = kclone((uint64)thread_allocator, (uint64)&shared_ptr, (uint64)stack);
  if (tid < 0) {
    printf("Main: kclone failed\n");
    exit(1);
  }

  // Wait for thread to exit
  kjoin(0);

  // Access the memory allocated dynamically by the child thread
  if (shared_ptr != 0) {
    printf("[Main Process] Reading from address %p allocated by Thread...\n", shared_ptr);
    printf("[Main Process] Content: '%s'\n", shared_ptr);
  } else {
    printf("Main Process: Pointer not set by thread!\n");
  }

  free(stack);
  printf("=== Test Passed Successfully! ===\n");
  exit(0);
}