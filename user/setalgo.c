#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int main(int argc, char *argv[]) {
  if (argc < 2) {
    printf("Usage: setalgo <fifo|lru>\n");
    exit(1);
  }

  if (strcmp(argv[1], "fifo") == 0) {
    set_algo(0);
    printf("Page Replacement Algorithm set to: FIFO (0)\n");
  } else if (strcmp(argv[1], "lru") == 0) {
    set_algo(1);
    printf("Page Replacement Algorithm set to: LRU (1)\n");
  } else {
    printf("Unknown algorithm. Use 'fifo' or 'lru'\n");
  }
  
  exit(0);
}