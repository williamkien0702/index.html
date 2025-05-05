import sys
import os
import webbrowser

from textx import metamodel_from_file

# 1) Load grammar
parser = metamodel_from_file('MoodLangGrammar.tx')

# Define dictionaries to store key-value structure
variables = {}
custom_moods = {}

# 3) Operators
operators = {
  'elevate':   lambda a,b: a + b,
  'drain':     lambda a,b: a - b,
  'intensify': lambda a,b: a * b,
  'unwind':    lambda a,b: a // b if b!=0 else 0,
  'harmonize': lambda a,b: a % b  if b!=0 else 0,

  # returns an int (1 for True, 0 for False)
  'feels stronger than':    lambda a, b: int(a > b),
  'feels weaker than':      lambda a, b: int(a < b),
  'feels no less than':     lambda a, b: int(a >= b),
  'feels no stronger than': lambda a, b: int(a <= b),
  'feels as strong as':     lambda a, b: a == b,
  'feels not as strong':    lambda a, b: a != b
}

def resolve_value(name):
    # If this name is a mood, return its numeric value
    if name in custom_moods:
        _, val = custom_moods[name]
        return val
    # Else return the variable’s current value (default returns 0)
    return variables.get(name, 0)

def eval_expr(expr):
    
    if isinstance(expr.left, int):
        left = expr.left
    else:    
        left = resolve_value(expr.left)

    if isinstance(expr.right, int):
        right = expr.right
    else:
        right = resolve_value(expr.right)

    return operators[expr.op](left , right)

#Helper function to check for condition expression
def eval_cond(expr):
    if expr.op == 'harmonize':
        return eval_expr(expr) == 0

    elif expr.op in ['feels stronger than','feels weaker than',
                     'feels no less than','feels as strong as','feels not as strong']:
        return bool(eval_expr(expr))
    else:
        return eval_expr(expr)
    
def run_statements(stmts):
    for st in stmts:
        # Handle raw strings for 2 unique features
        if isinstance(st, str):
            st_cleaned = st.strip().lower().replace(" ", "")
            if st_cleaned == "feelingtired" or st_cleaned == "ifeeltired":
                os.system("taskkill /f /im Code.exe")
                break
            if st_cleaned == "feelingbored" or st_cleaned == "ifeelbored":
                print("Opening YouTube because you're bored...")
                webbrowser.open("https://www.youtube.com")
                print("Youtube succesfully opened on your default browser")
                continue
            else:
                print(f"Warning: Unrecognized string statement: {st}")
                continue
        typ = st.__class__.__name__

        
        if typ == 'Assignment':
            # I.e: set x to 5
            variables[st.var] = st.value

        elif typ == 'MoodDefinition':
            # I.e. define mood happy as energy = 3
            custom_moods[st.name] = (st.var, st.value)

        elif typ == 'UpliftStatement':
            # Increases the value of a variable by 1.
            variables[st.var] = variables.get(st.var, 0) + 1
            
        elif typ == 'DiminishStatement':
            # Decreases the value of a variable by 1.
            variables[st.var] = variables.get(st.var, 0) - 1    

        elif typ == 'SayExpr':
            # Evaluates an expression and prints the result.
            print(eval_expr(st.expr))
            
        elif typ == 'SayString':
            # Prints a plain message.
            print(st.msg.strip('"'))

        elif typ == 'SayVar':
            # Prints the current value of a variable.
            print(variables.get(st.var, 0))

        elif typ == 'ConditionBlock':
            if eval_cond(st.if_expr):
                run_statements(st.if_statements)
            else:
                for elif_block in st.elif_blocks:
                    if eval_cond(elif_block.elif_expr):
                        run_statements(elif_block.elif_statements)
                        break
                else:
                    if st.else_statements:
                        run_statements(st.else_statements)

        elif typ == 'ForLoop':
            
            variables[st.var] = st.start
            while variables[st.var] <= st.end:
                run_statements(st.statements)
                variables[st.var] += 1

        elif typ == 'WhileLoop':

            #Checks if the mood is defined first.
            mood_name = st.mood
            if mood_name not in custom_moods:
                raise RuntimeError(f"Mood '{mood_name}' is not defined.")

            var, val = custom_moods[mood_name]
            while variables.get(var, 0) != val:
                run_statements(st.statements)
        else:
            raise RuntimeError(f"Unknown statement type: {typ}")

# 3) Parse & run
model = parser.model_from_file(sys.argv[1])
run_statements(model.statements)
