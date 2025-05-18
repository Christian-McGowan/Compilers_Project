# Simplified Rat24S Compiler

> A recursive‑descent parser and code generator for a simplified Rat24S language.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Repository Structure](#repository-structure)
4. [Usage](#usage)
5. [Assignment Specifications](#assignment-specifications)

   * [Syntax Analyzer Requirements](#syntax-analyzer-requirements)
   * [Part 1: Symbol Table Handling](#part-1-symbol-table-handling)
   * [Part 2: Assembly Code Generation](#part-2-assembly-code-generation)
6. [Virtual Machine Instruction Set](#virtual-machine-instruction-set)
7. [Testing](#testing)
8. [Example Output](#example-output)
9. [Notes](#notes)

---

## Overview

This project implements a compiler front end for a **simplified Rat24S** language, featuring:

* **No function definitions** and **no `real` type** (only `integer` and `boolean`).
* **Boolean** values: `true` → 1, `false` → 0.
* **Strict type checking**: disallow arithmetic on booleans and implicit conversions.

The compiler performs:

1. **Symbol Table Management**: declaration tracking, scope checking, type validation.
2. **Code Generation**: emission of labeled stack‑machine assembly instructions.

---

## Prerequisites

* **Python 3.7+** (no external dependencies)

---

## Repository Structure

```text
Compilers_Project/  (https://github.com/Christian-McGowan/Compilers_Project)
├── main.py            # Parser, semantic analyzer, and code generator
├── test1.rat25s       # Sample input 1
├── test2.rat25s       # Sample input 2
├── test3.rat25s       # Sample input 3
├── output1.txt        # Expected result for test1
├── output2.txt        # Expected result for test2
├── output3.txt        # Expected result for test3
└── README.md          # This document
```

---

## Usage

No compilation step required. Run the compiler as follows:

```bash
python3 main.py <source-file> > <output-file>
```

Example:

```bash
# Generate and compare output for test1
python3 main.py test1.rat25s > result1.txt
diff -u output1.txt result1.txt
```

---

## Assignment Specifications

### Syntax Analyzer Requirements

Building on Assignment 2, the parser must:

1. **Eliminate left recursion** and apply **left factoring** to the original Rat24S grammar.
2. **Reuse** the `lexer()` from Assignment 1 for tokenization.
3. **Log parsing**: print each token/lexeme and the production rule applied. Toggle via a debug switch.
4. **Error reporting**: on syntax error, output token, lexeme, line number, and error description.
5. **Complete parsing**: process syntactically correct programs in full.

#### Parsing Output Format

For each test case, the parser must emit output in the following structure, matching the sample exactly:

```text
=== Running Test Case: <filename>.rat25s ===

Tokens:
Token         Lexeme
----------------------
<type>        <lexeme>
...

Parsing Output:
<Nonterminal> -> <production>
Token: <Type> Lexeme: <lexeme>
...

Parsing complete.
```

* **Header**: `=== Running Test Case: <filename> ===`
* **Token listing**: under `Tokens:`, a two‐column table with a header row and separator line.
* **Production listing**: under `Parsing Output:`, print each production used and the corresponding token logs.
* **Footer**: `Parsing complete.`

<details>
<summary>Rewritten Grammar (R1–R29)</summary>

```bnf
R1.  <Rat25S> -> $$ <OptFuncDefs> $$ <OptDeclList> $$ <StmtList> $$
R2.  <OptFuncDefs> -> <FuncDefs> | ε
R3.  <FuncDefs> -> <Function> <FuncDefs’>
R3a. <FuncDefs’> -> <Function> <FuncDefs’> | ε
R4.  <Function> -> function <ID> ( <OptParamList> ) <OptDeclList> <Body>
R5.  <OptParamList> -> <ParamList> | ε
R6.  <ParamList> -> <Param> <ParamList’>
R6a. <ParamList’> -> , <Param> <ParamList’> | ε
R7.  <Param> -> <IDs> <Qualifier>
R8.  <Qualifier> -> integer | boolean | real
R9.  <Body> -> { <StmtList> }
R10. <OptDeclList> -> <DeclList> | ε
R11. <DeclList> -> <Declaration> ; <DeclList’>
R11a.<DeclList’> -> <Declaration> ; <DeclList’> | ε
R12. <Declaration> -> <Qualifier> <IDs>
R13. <IDs> -> <ID> <IDs’>
R13a.<IDs’> -> , <ID> <IDs’> | ε
R14. <StmtList> -> <Stmt> <StmtList’>
R14a.<StmtList’> -> <Stmt> <StmtList’> | ε
R15. <Stmt> -> <Compound> | <Assign> | <If> | <Return> | <Print> | <Scan> | <While>
R16. <Compound> -> { <StmtList> }
R17. <Assign> -> <ID> = <Expression> ;
R18. <If> -> if ( <Condition> ) <Stmt> <If’>
R18a.<If’> -> else <Stmt> endif | endif
R19. <Return> -> return ; | return <Expression> ;
R20. <Print> -> print ( <Expression> ) ;
R21. <Scan> -> scan ( <IDs> ) ;
R22. <While> -> while ( <Condition> ) <Stmt> endwhile
R23. <Condition> -> <Expression> <Relop> <Expression>
R24. <Relop> -> == | != | > | < | <= | =>
R25. <Expression> -> <Term> <Expr’>
R25a.<Expr’> -> + <Term> <Expr’> | - <Term> <Expr’> | ε
R26. <Term> -> <Factor> <Term’>
R26a.<Term’> -> * <Factor> <Term’> | / <Factor> <Term’> | ε
R27. <Factor> -> - <Primary> | <Primary>
R28. <Primary> -> <ID> | <Integer> | <ID> ( <IDs> ) | ( <Expression> ) | <Real> | true | false
R29. <Empty> -> ε
```

</details>

### Part 1: Symbol Table Handling (2%)

* **Memory Addresses**: start at 5000 and increment per declaration.
* **Operations**:

  * **Insert** new identifiers with lexeme, address, and type.
  * **Lookup** on use; error if undeclared.
  * **Prevent redeclaration**; error on duplicate.
* **Output**: after parsing, print a table:

  | Identifier | MemoryAddress | Type |
  | ---------- | ------------- | ---- |
  | ...        | ...           | ...  |

### Part 2: Assembly Code Generation (8%)

* **Instruction Buffer**: array of ≥1000 entries (indexed from 1).

* **Emission**: generate stack‑machine instructions for each AST node.

* **Listing**: print each instruction as:

  ```text
  <index> <OPCODE> [operands]
  ```

* **Followed by** the symbol table (as in Part 1).

---

## Virtual Machine Instruction Set

| Opcode | Operands | Description               |
| ------ | -------- | ------------------------- |
| PUSHI  | Int      | Push integer literal      |
| PUSHM  | Addr     | Push value from memory    |
| POPM   | Addr     | Pop and store into memory |
| SIN    | —        | Read integer from stdin   |
| SOUT   | —        | Pop and print value       |
| A      | —        | Add                       |
| S      | —        | Subtract (second – first) |
| M      | —        | Multiply                  |
| D      | —        | Divide (integer quotient) |
| GRT    | —        | Greater than check        |
| LES    | —        | Less than check           |
| EQU    | —        | Equality check            |
| NEQ    | —        | Inequality check          |
| GEQ    | —        | ≥ check                   |
| LEQ    | —        | ≤ check                   |
| JUMP   | Label    | Unconditional jump        |
| JUMP0  | Label    | Jump if top == 0          |
| LABEL  | —        | Label placeholder         |

---

## Testing

Verify against provided samples:

```bash
for i in 1 2 3; do
  python3 main.py test${i}.rat25s > result${i}.txt
  diff -u output${i}.txt result${i}.txt
done
```

All differences should be none.

---

## Example Output

See `output3.txt` for a complete sample. Key sections:

* **Token listing**
* **Production rules**
* **Symbol table**
* **Assembly listing**

