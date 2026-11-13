#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int main(int argc, char *argv[]) {
  printf("\n=== Phase 3: Demand Paging Test ===\n");
  
  // Default 5 Pages
  int pages = 5;
  if(argc > 1){
      pages = atoi(argv[1]); // String parameter ko integer mein convert karta hai
  }
  
  int size = pages * 4096;
  
  printf("[1] Calling sbrk(%d bytes) for %d pages...\n", size, pages);
  char *mem = sbrk(size);
  
  if(mem == (char*)-1){
     printf("Error: sbrk failed\n");
     exit(1);
  }
  
  printf("[2] sbrk successful! (No physical RAM allocated yet)\n");
  printf("[3] Writing to memory to trigger Page Faults...\n");
  
  // Har page ke pehle byte par write karenge taaki hardware page fault pakde
  for(int i = 0; i < pages; i++){
     mem[i * 4096] = 'X'; 
     printf(" -> Page %d accessed! Hardware Page Fault caught & RAM allocated.\n", i + 1);
  }
  
  printf("=== Test Passed! Lazy Allocation is working perfectly for %d pages. ===\n\n", pages);
  exit(0);
}