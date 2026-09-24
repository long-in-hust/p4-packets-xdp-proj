I want a tool that reads the json file in the specified path and use the discription here: https://github.com/p4lang/behavioral-model/blob/main/docs/JSON_format.md, find the total complexity (steps) and data sizes. Some notes:

Steps are calculated as follows:

- Register operations (read/write) counts as 2 steps
- Assignment operations counts as 1 step (if the right-hand side is a constant) or 2 steps (if the right-hand side is a variable)
- Each if/else check counts as 1 step (worse case is taken)
- Packet extraction counts as 1 step
- Packet emission counts as 1 step
- Each table application counts as 1 step