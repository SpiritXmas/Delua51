
# Delua51

Delua51 is a work in progress Lua 5.1 decompiler aimed towards compiled lua files with stripped debug information. Pull requests are welcome, anyone can contribute!




## Authors

- [@SpiritXmas](https://www.github.com/SpiritXmas)
  




## Todo list
- Implement basic blocks for cflow
- Finish implementing OP_CALL     (if c == 0) & (if b == 0)
- Finish implementing OP_RETURN   (if b == 0)
- Finish implementing OP_LOADBOOL (if c == 1)
- Add support for remaining opcodes
- Implement support for command line usage (input, output, display assembly and/or decompiled output)
- Work on actual output improvements after complete functionality (ie implementing inlining for Lua call setup moves, closure upvalue setups, etc)
