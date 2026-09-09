# Bacon-DB

Simple json-based database for small amount of schematic data.

## Context & Design

- Data is usually cached after "read" and uncached after "write", but mainly for parallelizm ease of access between threads, not efficiency
- There are multiple levels of abstraction as the design assumes "building blocks" from which the features are built:
  1. JSON handler
  1. Table Handler
  1. _TBD_
- When the library becomes mature, I will consider efficiency optimizations

### Limitations

- This library is not designed for huge amount of data (as JSON should __never__ be used for huge amount of data)
  - it is not optimized for efficiency
  - algorithms often go through all of the table rows
- Implementation assumes that each database file is handled by one handler (if at all)
  - multiple handlers used for the same file path __will__ lead to undefined behaviour
