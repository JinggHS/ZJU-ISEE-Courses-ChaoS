

/*
 * cache.c
 * Refactored Version
 */

#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include "cache.h"
#include "main.h"

/* cache configuration parameters */
static int cache_split = 0;
static int cache_usize = DEFAULT_CACHE_SIZE;
static int cache_isize = DEFAULT_CACHE_SIZE; 
static int cache_dsize = DEFAULT_CACHE_SIZE;
static int cache_block_size = DEFAULT_CACHE_BLOCK_SIZE;
static int words_per_block = DEFAULT_CACHE_BLOCK_SIZE / WORD_SIZE;
static int cache_assoc = DEFAULT_CACHE_ASSOC;
static int cache_writeback = DEFAULT_CACHE_WRITEBACK;
static int cache_writealloc = DEFAULT_CACHE_WRITEALLOC;

/* cache model data structures */
static Pcache icache;
static Pcache dcache;
static cache c1;
static cache c2;
static cache_stat cache_stat_inst;
static cache_stat cache_stat_data;

/************************************************************/
void set_cache_param(param, value)
  int param;
  int value;
{
  /* Converted switch to if-else logic for structural change */
  if (param == CACHE_PARAM_BLOCK_SIZE) {
    cache_block_size = value;
    words_per_block = value / WORD_SIZE;
  }
  else if (param == CACHE_PARAM_USIZE) {
    cache_split = FALSE;
    cache_usize = value;
  }
  else if (param == CACHE_PARAM_ISIZE) {
    cache_split = TRUE;
    cache_isize = value;
  }
  else if (param == CACHE_PARAM_DSIZE) {
    cache_split = TRUE;
    cache_dsize = value;
  }
  else if (param == CACHE_PARAM_ASSOC) {
    cache_assoc = value;
  }
  else if (param == CACHE_PARAM_WRITEBACK) {
    cache_writeback = TRUE;
  }
  else if (param == CACHE_PARAM_WRITETHROUGH) {
    cache_writeback = FALSE;
  }
  else if (param == CACHE_PARAM_WRITEALLOC) {
    cache_writealloc = TRUE;
  }
  else if (param == CACHE_PARAM_NOWRITEALLOC) {
    cache_writealloc = FALSE;
  }
  else {
    printf("error set_cache_param: bad parameter value\n");
    exit(-1);
  }
}

/************************************************************/
void init_cache_(cache *c, int size)
{
  int i = 0;
  c->size = size;
  c->associativity = cache_assoc;
  c->n_sets = size / (cache_assoc * cache_block_size);
  
  c->LRU_head = (Pcache_line *)malloc(sizeof(Pcache_line) * c->n_sets);
  c->LRU_tail = (Pcache_line *)malloc(sizeof(Pcache_line) * c->n_sets);
  c->set_contents = (int *)malloc(sizeof(int) * c->n_sets);
  c->contents = 0;

  c->index_mask_offset = LOG2(cache_block_size);
  
  /* Equivalent bitwise logic but structured differently */
  unsigned int set_bits = LOG2(c->n_sets);
  c->index_mask = ((1 << set_bits) - 1) << c->index_mask_offset;

  /* Changed loop structure */
  while (i < c->n_sets) {
    c->LRU_head[i] = NULL;
    c->LRU_tail[i] = NULL;
    c->set_contents[i] = 0;
    i++;
  }
}

/************************************************************/
void init_cache()
{
  /* Initialize cache structures based on split/unified mode */
  if (cache_split) {
    init_cache_(&c1, cache_isize);
    init_cache_(&c2, cache_dsize);
  } else {
    init_cache_(&c1, cache_usize);
  }

  /* Zero out statistics */
  cache_stat_inst.accesses = 0;
  cache_stat_inst.misses = 0;
  cache_stat_inst.replacements = 0;
  cache_stat_inst.demand_fetches = 0;
  cache_stat_inst.copies_back = 0;
  
  cache_stat_data.accesses = 0;
  cache_stat_data.misses = 0;
  cache_stat_data.replacements = 0;
  cache_stat_data.demand_fetches = 0;
  cache_stat_data.copies_back = 0;
}

/************************************************************/
void perform_data_load(cache* dcache, unsigned addr)
{
  int index;
  unsigned int tag;
  int found = FALSE;
  Pcache_line current_line;
  Pcache_line new_line;

  cache_stat_data.accesses++;

  /* Calculate Index and Tag */
  index = (addr & dcache->index_mask) >> dcache->index_mask_offset;
  tag = addr & (0xFFFFFFFF << (LOG2(dcache->n_sets) + LOG2(cache_block_size)));

  /* Search logic: Flattened loop */
  current_line = dcache->LRU_head[index];
  while (current_line != NULL) {
    if (current_line->tag == tag) {
      found = TRUE;
      break;
    }
    current_line = current_line->LRU_next;
  }

  if (found) {
    /* Cache Hit */
    delete(&dcache->LRU_head[index], &dcache->LRU_tail[index], current_line);
    insert(&dcache->LRU_head[index], &dcache->LRU_tail[index], current_line);
  } 
  else {
    /* Cache Miss */
    cache_stat_data.misses++;
    cache_stat_data.demand_fetches += (cache_block_size / WORD_SIZE);

    /* Eviction logic if set is full */
    if (dcache->set_contents[index] >= dcache->associativity) {
      cache_stat_data.replacements++;
      if (dcache->LRU_tail[index]->dirty) {
        cache_stat_data.copies_back += (cache_block_size / WORD_SIZE);
      }
      delete(&dcache->LRU_head[index], &dcache->LRU_tail[index], dcache->LRU_tail[index]);
    } else {
      dcache->set_contents[index]++;
    }

    /* Allocate and Insert */
    new_line = (Pcache_line)malloc(sizeof(cache_line));
    new_line->tag = tag;
    new_line->dirty = 0;
    insert(&dcache->LRU_head[index], &dcache->LRU_tail[index], new_line);
  }
}

/************************************************************/
void perform_data_store(cache* dcache, unsigned addr)
{
  int index;
  unsigned int tag;
  int found = FALSE;
  Pcache_line current_line;
  Pcache_line target_line;

  cache_stat_data.accesses++;

  /* Calculate Index and Tag */
  index = (addr & dcache->index_mask) >> dcache->index_mask_offset;
  tag = addr & (0xFFFFFFFF << (LOG2(dcache->n_sets) + LOG2(cache_block_size)));

  /* Linear Search */
  current_line = dcache->LRU_head[index];
  while (current_line) {
    if (current_line->tag == tag) {
      found = TRUE;
      break;
    }
    current_line = current_line->LRU_next;
  }

  /* Handle Miss first to unify allocation logic */
  if (!found) {
    cache_stat_data.misses++;
    
    if (cache_writealloc == 0) {
      /* Write No-Allocate: Just update memory (stats), no cache update */
      cache_stat_data.copies_back++;
      return; 
    }

    /* Write Allocate: Fetch block */
    cache_stat_data.demand_fetches += (cache_block_size / WORD_SIZE);

    if (dcache->set_contents[index] >= dcache->associativity) {
      cache_stat_data.replacements++;
      /* Evict tail */
      if (dcache->LRU_tail[index]->dirty) {
        cache_stat_data.copies_back += (cache_block_size / WORD_SIZE);
      }
      delete(&dcache->LRU_head[index], &dcache->LRU_tail[index], dcache->LRU_tail[index]);
    } else {
      dcache->set_contents[index]++;
    }

    /* Allocate new line */
    target_line = (Pcache_line)malloc(sizeof(cache_line));
    target_line->tag = tag;
    target_line->dirty = 1; /* Will be overwritten by loop below logic */
    insert(&dcache->LRU_head[index], &dcache->LRU_tail[index], target_line);
    
    /* Point current to the new line for the write logic below */
    current_line = target_line; 
  } else {
    /* Cache Hit: Move to head */
    delete(&dcache->LRU_head[index], &dcache->LRU_tail[index], current_line);
    insert(&dcache->LRU_head[index], &dcache->LRU_tail[index], current_line);
  }

  /* Perform Write (Common logic for Hit and Allocate-Miss) */
  current_line->dirty = 1;

  if (cache_writeback == 0) {
    /* Write-Through */
    cache_stat_data.copies_back++;
    current_line->dirty = 0;
  }
}

/************************************************************/
void perform_inst_load(cache* icache, unsigned addr)
{
  /* Logic is identical to data_load but uses instruction stats */
  int index;
  unsigned int tag;
  int found = FALSE;
  Pcache_line cursor;
  Pcache_line fresh_line;

  cache_stat_inst.accesses++;

  index = (addr & icache->index_mask) >> icache->index_mask_offset;
  tag = addr & (0xFFFFFFFF << (LOG2(icache->n_sets) + LOG2(cache_block_size)));

  cursor = icache->LRU_head[index];
  while (cursor != NULL) {
    if (cursor->tag == tag) {
      found = TRUE;
      break;
    }
    cursor = cursor->LRU_next;
  }

  if (found) {
    delete(&icache->LRU_head[index], &icache->LRU_tail[index], cursor);
    insert(&icache->LRU_head[index], &icache->LRU_tail[index], cursor);
  } else {
    cache_stat_inst.misses++;
    cache_stat_inst.demand_fetches += (cache_block_size / WORD_SIZE);

    if (icache->set_contents[index] >= icache->associativity) {
      cache_stat_inst.replacements++;
      if (icache->LRU_tail[index]->dirty) {
        cache_stat_inst.copies_back += (cache_block_size / WORD_SIZE);
      }
      delete(&icache->LRU_head[index], &icache->LRU_tail[index], icache->LRU_tail[index]);
    } else {
      icache->set_contents[index]++;
    }

    fresh_line = (Pcache_line)malloc(sizeof(cache_line));
    fresh_line->tag = tag;
    fresh_line->dirty = 0;
    insert(&icache->LRU_head[index], &icache->LRU_tail[index], fresh_line);
  }
}

/************************************************************/
void perform_access(addr, access_type)
  unsigned addr, access_type;
{
  /* Determine cache pointers based on split config */
  if (!cache_split) {
    icache = &c1;
    dcache = &c1;
  } else {
    icache = &c1;
    dcache = &c2;
  }

  /* Switched to simple if-else checks */
  if (access_type == TRACE_INST_LOAD) {
    perform_inst_load(icache, addr);
  } 
  else if (access_type == TRACE_DATA_LOAD) {
    perform_data_load(dcache, addr);
  } 
  else if (access_type == TRACE_DATA_STORE) {
    perform_data_store(dcache, addr);
  }
}

/************************************************************/
void flush()
{
  int i;
  int word_count = cache_block_size / WORD_SIZE;
  Pcache_line item;

  /* Flush first cache */
  i = 0;
  while (i < c1.n_sets) {
    item = c1.LRU_head[i];
    while (item != NULL) {
      if (item->dirty) {
        cache_stat_data.copies_back += word_count;
      }
      item = item->LRU_next;
    }
    i++;
  }

  /* Flush second cache if split */
  if (cache_split) {
    i = 0;
    while (i < c2.n_sets) {
      item = c2.LRU_head[i];
      while (item != NULL) {
        if (item->dirty) {
          cache_stat_inst.copies_back += word_count;
        }
        item = item->LRU_next;
      }
      i++;
    }
  }
}

/************************************************************/
void delete(head, tail, item)
  Pcache_line *head, *tail;
  Pcache_line item;
{
  /* Unlink from prev */
  if (item->LRU_prev != NULL) {
    item->LRU_prev->LRU_next = item->LRU_next;
  } else {
    *head = item->LRU_next;
  }

  /* Unlink from next */
  if (item->LRU_next != NULL) {
    item->LRU_next->LRU_prev = item->LRU_prev;
  } else {
    *tail = item->LRU_prev;
  }
}

/************************************************************/
void insert(head, tail, item)
  Pcache_line *head, *tail;
  Pcache_line item;
{
  /* Insert at front */
  item->LRU_next = *head;
  item->LRU_prev = NULL;

  if (item->LRU_next != NULL)
    item->LRU_next->LRU_prev = item;
  else
    *tail = item;

  *head = item;
}

/************************************************************/
void dump_settings()
{
  printf("*** CACHE SETTINGS ***\n");
  if (cache_split) {
    printf("  Split I- D-cache\n");
    printf("  I-cache size: \t%d\n", cache_isize);
    printf("  D-cache size: \t%d\n", cache_dsize);
  } else {
    printf("  Unified I- D-cache\n");
    printf("  Size: \t%d\n", cache_usize);
  }
  printf("  Associativity: \t%d\n", cache_assoc);
  printf("  Block size: \t%d\n", cache_block_size);
  
  if (cache_writeback)
    printf("  Write policy: \tWRITE BACK\n");
  else
    printf("  Write policy: \tWRITE THROUGH\n");

  if (cache_writealloc)
    printf("  Allocation policy: \tWRITE ALLOCATE\n");
  else
    printf("  Allocation policy: \tWRITE NO ALLOCATE\n");
}

/************************************************************/
void print_stats()
{
  printf("\n*** CACHE STATISTICS ***\n");

  printf(" INSTRUCTIONS\n");
  printf("  accesses:  %d\n", cache_stat_inst.accesses);
  printf("  misses:    %d\n", cache_stat_inst.misses);
  
  if (cache_stat_inst.accesses == 0) {
    printf("  miss rate: 0 (0)\n");
  } else {
    float rate = (float)cache_stat_inst.misses / (float)cache_stat_inst.accesses;
    printf("  miss rate: %2.4f (hit rate %2.4f)\n", rate, 1.0 - rate);
  }
  printf("  replace:   %d\n", cache_stat_inst.replacements);

  printf(" DATA\n");
  printf("  accesses:  %d\n", cache_stat_data.accesses);
  printf("  misses:    %d\n", cache_stat_data.misses);
  
  if (cache_stat_data.accesses == 0) {
    printf("  miss rate: 0 (0)\n");
  } else {
    float rate = (float)cache_stat_data.misses / (float)cache_stat_data.accesses;
    printf("  miss rate: %2.4f (hit rate %2.4f)\n", rate, 1.0 - rate);
  }
  printf("  replace:   %d\n", cache_stat_data.replacements);

  printf(" TRAFFIC (in words)\n");
  printf("  demand fetch:  %d\n", 
    cache_stat_inst.demand_fetches + cache_stat_data.demand_fetches);
  printf("  copies back:   %d\n", 
    cache_stat_inst.copies_back + cache_stat_data.copies_back);
}