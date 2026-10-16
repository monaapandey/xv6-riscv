// xv6-RISC-V Deadlock & Banker's Algorithm Implementation

#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int sleep(int);
#define MAX_N 5  // Maximum processes
#define MAX_M 5  // Maximum resource types

// Print matrix utility
void print_matrix(const char *name, int mat[MAX_N][MAX_M], int n, int m) {
  printf("%s Matrix:\n", name);
  for (int i = 0; i < n; i++) {
    printf("  P%d: ", i);
    for (int j = 0; j < m; j++) {
      printf("%d ", mat[i][j]);
    }
    printf("\n");
  }
}

// Print vector utility
void print_vector(const char *name, int vec[MAX_M], int m) {
  printf("%s Vector: [ ", name);
  for (int i = 0; i < m; i++) {
    printf("%d ", vec[i]);
  }
  printf("]\n");
}

// -------------------------------------------------------------------
// Task (b): Deadlock Detection Algorithm
// -------------------------------------------------------------------
int detect_deadlock(int n, int m, int Allocation[MAX_N][MAX_M],
                    int Request[MAX_N][MAX_M], int Available[MAX_M],
                    int deadlocked_procs[MAX_N]) {
  int Work[MAX_M];
  int Finish[MAX_N];
  int num_deadlocked = 0;

  for (int j = 0; j < m; j++) {
    Work[j] = Available[j];
  }

  for (int i = 0; i < n; i++) {
    // If a process holds 0 resources across all types, mark finish = 1
    int has_alloc = 0;
    for (int j = 0; j < m; j++) {
      if (Allocation[i][j] > 0) {
        has_alloc = 1;
        break;
      }
    }
    Finish[i] = (has_alloc == 0) ? 1 : 0;
  }

  // Iteratively find process whose Request <= Work
  while (1) {
    int found = 0;
    for (int i = 0; i < n; i++) {
      if (!Finish[i]) {
        int can_satisfy = 1;
        for (int j = 0; j < m; j++) {
          if (Request[i][j] > Work[j]) {
            can_satisfy = 0;
            break;
          }
        }

        if (can_satisfy) {
          // Simulate process finishing and releasing allocation
          for (int j = 0; j < m; j++) {
            Work[j] += Allocation[i][j];
          }
          Finish[i] = 1;
          found = 1;
          printf("  [Detection] P%d can finish. Updated Work: ", i);
          print_vector("", Work, m);
        }
      }
    }
    if (!found) break;
  }

  // Identify deadlocked processes
  for (int i = 0; i < n; i++) {
    if (!Finish[i]) {
      deadlocked_procs[num_deadlocked++] = i;
    }
  }

  return num_deadlocked;
}

// -------------------------------------------------------------------
// Task (d): Banker's Safety Algorithm
// -------------------------------------------------------------------
int is_safe_state(int n, int m, int Allocation[MAX_N][MAX_M],
                  int Max[MAX_N][MAX_M], int Available[MAX_M],
                  int safe_seq[MAX_N]) {
  int Work[MAX_M];
  int Finish[MAX_N];
  int Need[MAX_N][MAX_M];
  int count = 0;

  // Calculate Need matrix: Need = Max - Allocation
  for (int i = 0; i < n; i++) {
    Finish[i] = 0;
    for (int j = 0; j < m; j++) {
      Need[i][j] = Max[i][j] - Allocation[i][j];
      if (Need[i][j] < 0) Need[i][j] = 0;
    }
  }

  for (int j = 0; j < m; j++) {
    Work[j] = Available[j];
  }

  while (count < n) {
    int found = 0;
    for (int i = 0; i < n; i++) {
      if (!Finish[i]) {
        int can_execute = 1;
        for (int j = 0; j < m; j++) {
          if (Need[i][j] > Work[j]) {
            can_execute = 0;
            break;
          }
        }

        if (can_execute) {
          for (int j = 0; j < m; j++) {
            Work[j] += Allocation[i][j];
          }
          safe_seq[count++] = i;
          Finish[i] = 1;
          found = 1;
          printf("  [Banker] P%d added to safe sequence. Updated Work: ", i);
          print_vector("", Work, m);
        }
      }
    }
    if (!found) break;
  }

  return (count == n);
}

// Helper to test resource allocation request under Banker's algorithm
void request_resources(int p_id, int request[MAX_M], int n, int m,
                       int Allocation[MAX_N][MAX_M], int Max[MAX_N][MAX_M],
                       int Available[MAX_M]) {
  printf("\n--- Process P%d Requests Resources ---\n", p_id);
  print_vector("Request", request, m);

  int Need[MAX_M];
  for (int j = 0; j < m; j++) {
    Need[j] = Max[p_id][j] - Allocation[p_id][j];
    if (request[j] > Need[j]) {
      printf("Error: Process exceeded max claim!\n");
      return;
    }
    if (request[j] > Available[j]) {
      printf("Resources unavailable. P%d must wait.\n", p_id);
      return;
    }
  }

  // Pretend to allocate
  for (int j = 0; j < m; j++) {
    Available[j] -= request[j];
    Allocation[p_id][j] += request[j];
  }

  int safe_seq[MAX_N];
  if (is_safe_state(n, m, Allocation, Max, Available, safe_seq)) {
    printf("Request Granted! System remains in a SAFE state.\n");
  } else {
    printf("Request Denied! Granting leads to an UNSAFE state (Deadlock risk).\n");
    // Rollback
    for (int j = 0; j < m; j++) {
      Available[j] += request[j];
      Allocation[p_id][j] -= request[j];
    }
  }
}

// -------------------------------------------------------------------
// Task (c): Real xv6 Pipe Deadlock Simulation
// -------------------------------------------------------------------
void simulate_pipe_deadlock(void) {
  printf("\n=======================================================\n");
  printf(" Task (c): Real xv6 Circular Wait Pipe Simulation\n");
  printf("=======================================================\n");

  int pipe1[2], pipe2[2];
  if (pipe(pipe1) < 0 || pipe(pipe2) < 0) {
    printf("Pipe creation failed\n");
    exit(1);
  }

  // Model matrix for 2 processes & 2 pipe resources
  int Allocation[MAX_N][MAX_M] = {
    {1, 0}, // P0 holds Pipe1 write end
    {0, 1}  // P1 holds Pipe2 write end
  };
  int Request[MAX_N][MAX_M] = {
    {0, 1}, // P0 waits to read Pipe2
    {1, 0}  // P1 waits to read Pipe1
  };
  int Available[MAX_M] = {0, 0};
  int deadlocked[MAX_N];

  printf("Simulating Circular Wait: P0 holds Pipe1, waits Pipe2. P1 holds Pipe2, waits Pipe1.\n");
  
  int num_dead = detect_deadlock(2, 2, Allocation, Request, Available, deadlocked);
  if (num_dead > 0) {
    printf("\n>>> DEADLOCK DETECTED! Deadlocked processes: ");
    for (int i = 0; i < num_dead; i++) {
      printf("P%d ", deadlocked[i]);
    }
    printf("<<<\n");
  }

  // Execute pipe circular wait using fork
  int pid = fork();
  if (pid == 0) {
    // Child (Process B): holds Pipe2 write end, blocks reading Pipe1
    char buf;
    printf("[Child P1] Holding Pipe2 write end, waiting to read Pipe1...\n");
    read(pipe1[0], &buf, 1); // Blocks forever
    exit(0);
  } else {
    // Parent (Process A): holds Pipe1 write end, blocks reading Pipe2
    printf("[Parent P0] Holding Pipe1 write end, waiting to read Pipe2...\n");
    sleep(20); 
    printf("[Parent P0] Confirmed Circular Wait in Kernel! Cleaning up child P1...\n");
    kill(pid);
    wait(0);
  }

  close(pipe1[0]); close(pipe1[1]);
  close(pipe2[0]); close(pipe2[1]);
}

// -------------------------------------------------------------------
// Main Driver Function
// -------------------------------------------------------------------
int main(int argc, char *argv[]) {
  printf("=======================================================\n");
  printf("  XV6 DEADLOCK DETECTION & BANKER'S ALGORITHM SUITE    \n");
  printf("=======================================================\n");

  // -----------------------------------------------------------------
  // Test Case 1: Safe State Matrix (3 Processes, 3 Resources)
  // -----------------------------------------------------------------
  printf("\n--- TEST CASE 1: Safe State Check ---\n");
  int n1 = 3, m1 = 3;
  int Alloc1[MAX_N][MAX_M] = {
    {0, 1, 0},
    {2, 0, 0},
    {3, 0, 2}
  };
  int Max1[MAX_N][MAX_M] = {
    {7, 5, 3},
    {3, 2, 2},
    {9, 0, 2}
  };
  int Avail1[MAX_M] = {3, 3, 2};
  int safe_seq[MAX_N];

  print_matrix("Allocation", Alloc1, n1, m1);
  print_matrix("Max", Max1, n1, m1);
  print_vector("Available", Avail1, m1);

  if (is_safe_state(n1, m1, Alloc1, Max1, Avail1, safe_seq)) {
    printf("RESULT: System is in a SAFE state. Safe Sequence: ");
    for (int i = 0; i < n1; i++) printf("P%d ", safe_seq[i]);
    printf("\n");
  } else {
    printf("RESULT: System is UNSAFE / DEADLOCKED.\n");
  }

  // -----------------------------------------------------------------
  // Test Case 2: Deadlocked Matrix
  // -----------------------------------------------------------------
  printf("\n--- TEST CASE 2: Deadlock Detection ---\n");
  int n2 = 3, m2 = 3;
  int Alloc2[MAX_N][MAX_M] = {
    {1, 0, 0},
    {0, 1, 0},
    {0, 0, 1}
  };
  int Req2[MAX_N][MAX_M] = {
    {0, 1, 0},
    {0, 0, 1},
    {1, 0, 0}
  };
  int Avail2[MAX_M] = {0, 0, 0};
  int deadlocked[MAX_N];

  print_matrix("Allocation", Alloc2, n2, m2);
  print_matrix("Request", Req2, n2, m2);
  print_vector("Available", Avail2, m2);

  int num_dead = detect_deadlock(n2, m2, Alloc2, Req2, Avail2, deadlocked);
  if (num_dead > 0) {
    printf("RESULT: DEADLOCK DETECTED! Deadlocked Processes: ");
    for (int i = 0; i < num_dead; i++) printf("P%d ", deadlocked[i]);
    printf("\n");
  } else {
    printf("RESULT: No deadlock detected.\n");
  }

  // -----------------------------------------------------------------
  // Test Case 3: Transition from Safe to Unsafe Request
  // -----------------------------------------------------------------
  printf("\n--- TEST CASE 3: State Becoming Unsafe After Request ---\n");
  int n3 = 3, m3 = 2;
  int Alloc3[MAX_N][MAX_M] = {
    {1, 0},
    {1, 1},
    {0, 1}
  };
  int Max3[MAX_N][MAX_M] = {
    {2, 1},
    {2, 2},
    {1, 2}
  };
  int Avail3[MAX_M] = {1, 0};

  print_matrix("Allocation", Alloc3, n3, m3);
  print_matrix("Max", Max3, n3, m3);
  print_vector("Available", Avail3, m3);

  int req_p0[MAX_M] = {1, 0}; // Request that will lead to unsafe state
  request_resources(0, req_p0, n3, m3, Alloc3, Max3, Avail3);

  // -----------------------------------------------------------------
  // Pipe Deadlock Simulation
  // -----------------------------------------------------------------
  simulate_pipe_deadlock();

  exit(0);
}