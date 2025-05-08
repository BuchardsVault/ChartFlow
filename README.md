# ChartFlow DSL

A simple domain‑specific language for fetching financial data and rendering tables or charts, built with TextX and Python.

## Overview

ChartFlow lets you:

- **Show** raw price data for one or more assets over a given date range.
- **Chart** that data as a candlestick, line, OHLC, or bar chart, with customizable options.
- **Let** bindings to store intermediate lists or values in variables.

The grammar is defined in \`chartFlow.tx\` and the interpreter is in \`src/interpreter.py\`.

## Syntax

### Statements

\`\`\`ebnf
Model:
    statements*=Statement
;

Statement:
      ShowStmt      // print raw data
    | ChartStmt     // render charts
    | LetStmt       // variable assignment
;
\`\`\`

- **ShowStmt**: Dump raw data.  
- **ChartStmt**: Render a chart.  
- **LetStmt**: Bind an expression to a name.

### Show Statement

\`\`\`ebnf
ShowStmt:
    'show' asset=AssetSpec date=DateClause
;
\`\`\`

Prints a table of historical data for the given asset(s).

### Chart Statement

\`\`\`ebnf
ChartStmt:
    'chart' asset=AssetSpec date=DateClause
    ('as' charttype=ChartType)?
    ('with' options+=Option[','])?
;
\`\`\`

- **as**: Optional chart type: \`candlestick\`, \`line\`, \`ohlc\`, or \`bar\`.  
- **with**: Key/value options, e.g. \`width=800\`, \`height=600\`, \`title="My Chart"\`.

### Let Statement

\`\`\`ebnf
LetStmt:
    'let' name=ID '=' expr=Expr
;
\`\`\`

Binds \`expr\` (a list, literal, or function call) to \`name\` for reuse.

## Asset Specification

\`\`\`ebnf
AssetSpec:
      symbol=STRING            // Single ticker, e.g. "AAPL"
    | '[' symbols+=STRING[','] ']'  // List of tickers, e.g. ["AAPL","GOOG"]
    | var=ID                   // Variable reference, e.g. myAssets
;
\`\`\`

Supports single symbols, lists, or previously bound variables.

## Date Clauses

\`\`\`ebnf
DateClause:
      'from' start=Date 'to' end=Date  // Explicit range, e.g. from 2024-01-01 to 2024-03-31
    | 'in'  year=INT                   // Whole year, e.g. in 2024
    | 'last' days=INT ('days'|'weeks')  // Relative, e.g. last 30 days, last 4 weeks
;
\`\`\`

Dates follow \`YYYY-MM-DD\` or just \`YYYY\`.

## Expressions

\`\`\`ebnf
Expr:
      List
    | Literal
    | FunctionCall
    | ID
;

List:
    '[' elements+=Expr[','] ']'
;

FunctionCall:
    name=ID '(' args+=Expr[','] ')'
;

Literal:
    STRING | INT | FLOAT
;
\`\`\`

- **Lists**: Python‑style lists of expressions.  
- **Function calls**: e.g. \`moving_avg(["AAPL"], 20)\`.  
- **IDs**: References to variables.

## Chart Types & Options

- **ChartType**: \`candlestick\` \| \`line\` \| \`ohlc\` \| \`bar\`  
- **Option**: \`key=value\`, where \`value\` can be string, int, float, or list.

Example options:

\`\`\`text
with width=800, height=400, title="Q1 Performance"
\`\`\`

## Code Structure

- **Grammar**: \`grammar/chartFlow.tx\` defines the syntax via TextX.  
- **Interpreter**: \`src/interpreter.py\` registers the metamodel, parses a \`.cf\` file, and executes the AST.  
  1. **Parsing**: TextX builds an object model from the input.  
  2. **Execution**: We walk the model, handling \`LetStmt\`, \`ShowStmt\`, and \`ChartStmt\`.

### Key Components

- **Metamodel**: \`textx.metamodel_from_file("grammar/chartFlow.tx")\`.  
- **Context**: A dict storing variable bindings.  
- **Data Fetching**: Uses \`yfinance\` wrapped in \`src/data_fetcher.py\`.  
- **Rendering**: Uses Matplotlib and \`tabulate\` in \`src/renderer.py\`.

## Examples

\`\`\`cf
# Bind a list of tickers
let tech = ["AAPL","GOOG","MSFT"]

# Show raw data for tech stocks over Q1 2024
show tech from 2024-01-01 to 2024-03-31

# Render a line chart for AAPL price last 30 days
chart "AAPL" last 30 days as line with width=800, height=300
\`\`\`

## Running

1. Install dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`
2. Run interpreter:
   \`\`\`bash
   python -m chartflow.interpreter examples/basic_show.cf
   \`\`\`

---
